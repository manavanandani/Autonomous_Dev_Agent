"""
Utility functions for working with LLMs in the Autonomous Software Development Agent.
"""
import os
from typing import Dict, Any, List, Optional
from types import SimpleNamespace
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field

from autonomous_dev_agent.src.config.config import settings


def get_openai_llm(model: Optional[str] = None, temperature: Optional[float] = None):
    """
    Get an OpenAI LLM instance with the specified configuration.
    
    Args:
        model: The model name to use (defaults to config setting)
        temperature: The temperature setting (defaults to config setting)
        
    Returns:
        An instance of ChatOpenAI
    """
    model = model or settings.DEFAULT_LLM_MODEL
    temperature = temperature if temperature is not None else settings.TEMPERATURE
    
    # Check both settings and direct OS environment for DRY_RUN
    if settings.DRY_RUN or os.getenv("DRY_RUN", "false").lower() == "true":
        return SimpleNamespace(dry_run=True)
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Provide it in .env or enable DRY_RUN to skip external calls.")
    return ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=model,
        temperature=temperature,
    )


def get_anthropic_llm(model: Optional[str] = None, temperature: Optional[float] = None):
    """
    Get an Anthropic LLM instance with the specified configuration.
    
    Args:
        model: The model name to use (defaults to "claude-3-opus-20240229")
        temperature: The temperature setting (defaults to config setting)
        
    Returns:
        An instance of ChatAnthropic
    """
    model = model or "claude-3-opus-20240229"
    temperature = temperature if temperature is not None else settings.TEMPERATURE
    
    return ChatAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        model=model,
        temperature=temperature,
    )


def create_structured_output_chain(llm, prompt_template, output_schema):
    """
    Create a chain that produces structured output according to the given schema.
    
    Args:
        llm: The language model to use
        prompt_template: The prompt template string or ChatPromptTemplate
        output_schema: Pydantic model defining the output structure
        
    Returns:
        A chain that can be invoked to produce structured output
    """
    if isinstance(prompt_template, str):
        prompt = ChatPromptTemplate.from_template(prompt_template)
    else:
        prompt = prompt_template
        
    if getattr(llm, "dry_run", False) or settings.DRY_RUN:
        class DryRunChain:
            def invoke(self, _inputs: Dict[str, Any]):
                defaults: Dict[str, Any] = {}
                field_names = set(getattr(output_schema, "__fields__", {}).keys()) or set()
                if "requirements" in field_names:
                    defaults["requirements"] = [{"id": "DRYRUN", "description": "Dry Run", "priority": "high", "tags": [], "dependencies": []}]
                if "tasks" in field_names:
                    # Generate more realistic task based on the input
                    input_text = ""
                    if "description" in _inputs:
                        input_text = _inputs["description"].lower()
                    
                    if "add" in input_text and "number" in input_text:
                        task_desc = "Create a function to add two numbers with user input"
                    elif "calculator" in input_text:
                        task_desc = "Build a calculator with basic arithmetic operations"
                    else:
                        task_desc = "Dry Run"
                    
                    defaults["tasks"] = [{"id": "DRYRUN", "title": "Code Generation", "description": task_desc, "requirement_ids": ["DRYRUN"], "priority": "high", "dependencies": [], "estimated_effort": "1h", "status": "pending"}]
                if "code_snippets" in field_names:
                    # Generate more realistic code based on the input
                    # Check for description in various possible locations
                    input_text = ""
                    if "description" in _inputs:
                        input_text = _inputs["description"].lower()
                    elif "task" in _inputs and hasattr(_inputs["task"], "description"):
                        input_text = _inputs["task"].description.lower()
                    elif "tasks" in _inputs and len(_inputs["tasks"]) > 0:
                        task = _inputs["tasks"][0]
                        if isinstance(task, dict):
                            input_text = task.get("description", "").lower()
                        else:
                            input_text = task.description.lower()
                    
                    # Also check task description if available
                    if "description" in _inputs:
                        task_desc = _inputs["description"].lower()
                        if "add" in task_desc and "number" in task_desc:
                            input_text = task_desc
                        elif "function" in task_desc and "add" in task_desc:
                            input_text = task_desc
                    
                    # For demo purposes, always generate add numbers code in dry-run mode
                    code_content = """def add_numbers(a, b):
    \"\"\"Add two numbers and return the result.\"\"\"
    return a + b

# Example usage
if __name__ == "__main__":
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))
    result = add_numbers(num1, num2)
    print(f"The sum of {num1} and {num2} is {result}")"""
                    
                    defaults["code_snippets"] = [{"id": "DRYRUN", "title": "Generated Code", "code": code_content, "language": "python", "file_path": "main.py", "dependencies": []}]
                if "test_cases" in field_names:
                    defaults["test_cases"] = [{"id": "DRYRUN", "title": "Dry Run", "description": "Dry Run", "test_code": "assert True", "expected_output": "DRYRUN", "status": "pending"}]
                if {"review_passed", "issues", "suggestions"}.issubset(field_names):
                    defaults.update({"review_passed": True, "issues": [], "suggestions": []})
                if {"fixed_code", "changes_made", "confidence"}.issubset(field_names):
                    defaults.update({"fixed_code": "", "changes_made": [], "confidence": 0.0})
                if "documentation" in field_names:
                    defaults["documentation"] = {"id": "DOC-DRYRUN", "title": "Dry Run", "content": "", "code_snippet_ids": [], "doc_type": "technical"}
                try:
                    # Try to create the Pydantic object with defaults
                    return output_schema(**defaults)
                except Exception as e:
                    # If schema creation fails, try with minimal required fields
                    try:
                        # Get required fields from the schema
                        required_fields = {}
                        if hasattr(output_schema, '__fields__'):
                            for field_name, field_info in output_schema.__fields__.items():
                                if field_info.is_required():
                                    if field_name == 'id':
                                        required_fields[field_name] = 'DRYRUN'
                                    elif field_name == 'description':
                                        required_fields[field_name] = 'Dry Run'
                                    elif field_name == 'title':
                                        required_fields[field_name] = 'Dry Run'
                                    else:
                                        required_fields[field_name] = defaults.get(field_name, 'Dry Run')
                        return output_schema(**required_fields)
                    except Exception:
                        # Last resort: return a simple object
                        from types import SimpleNamespace
                        return SimpleNamespace(**defaults)
        return DryRunChain()
    parser = JsonOutputParser(pydantic_object=output_schema)
    chain = prompt | llm | parser
    return chain


def create_text_output_chain(llm, prompt_template):
    """
    Create a chain that produces text output.
    
    Args:
        llm: The language model to use
        prompt_template: The prompt template string or ChatPromptTemplate
        
    Returns:
        A chain that can be invoked to produce text output
    """
    if isinstance(prompt_template, str):
        prompt = ChatPromptTemplate.from_template(prompt_template)
    else:
        prompt = prompt_template
        
    if getattr(llm, "dry_run", False) or settings.DRY_RUN:
        class DryRunChain:
            def invoke(self, _inputs: Dict[str, Any]):
                return "DRY_RUN"
        return DryRunChain()
    parser = StrOutputParser()
    chain = prompt | llm | parser
    return chain
