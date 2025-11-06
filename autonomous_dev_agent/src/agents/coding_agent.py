"""
Coding agent for generating code based on technical tasks.
"""
from typing import Dict, Any, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import TechnicalTask, CodeSnippet
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain, create_text_output_chain
from autonomous_dev_agent.src.config.config import settings


class CodeGenerationOutput(BaseModel):
    """
    Output schema for code generation.
    """
    code_snippets: List[Dict[str, Any]] = Field(
        description="List of generated code snippets for the technical task"
    )


class CodeReviewOutput(BaseModel):
    """
    Output schema for code review.
    """
    review_passed: bool = Field(
        description="Whether the code passes the review"
    )
    issues: List[str] = Field(
        description="List of issues found in the code"
    )
    suggestions: List[str] = Field(
        description="List of suggestions for improving the code"
    )


class CodingAgent(BaseAgent):
    """
    Agent responsible for generating code based on technical tasks.
    """
    
    def __init__(self, agent_id: str = "coding_agent"):
        """
        Initialize the coding agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        super().__init__(agent_id, "coding")
        self.llm = get_openai_llm(model=settings.CODE_LLM_MODEL)
        
        # Initialize chains
        self._init_code_generation_chain()
        self._init_code_review_chain()
        self._init_code_improvement_chain()
    
    def _init_code_generation_chain(self):
        """
        Initialize the chain for generating code based on technical tasks.
        """
        template = """
        You are an expert software developer. Your task is to generate high-quality code
        based on the following technical task:
        
        Task ID: {task_id}
        Title: {title}
        Description: {description}
        
        Additional context:
        {context}
        
        For each code snippet:
        1. Assign a unique ID
        2. Write clean, well-documented code
        3. Specify the programming language
        4. Suggest an appropriate file path
        5. Add a brief description of what the code does
        
        Return the code snippets in a structured format.
        """
        
        self.code_generation_chain = create_structured_output_chain(
            self.llm,
            template,
            CodeGenerationOutput
        )
    
    def _init_code_review_chain(self):
        """
        Initialize the chain for reviewing generated code.
        """
        template = """
        You are an expert code reviewer. Your task is to review the following code
        and identify any issues or areas for improvement:
        
        Code:
        ```{language}
        {code}
        ```
        
        Task context:
        {task_description}
        
        Perform a thorough review considering:
        1. Correctness - Does the code correctly implement the requirements?
        2. Efficiency - Is the code efficient in terms of time and space complexity?
        3. Readability - Is the code easy to read and understand?
        4. Maintainability - Is the code easy to maintain and extend?
        5. Security - Are there any security vulnerabilities?
        6. Best practices - Does the code follow industry best practices?
        
        Return your review in a structured format.
        """
        
        self.code_review_chain = create_structured_output_chain(
            self.llm,
            template,
            CodeReviewOutput
        )
    
    def _init_code_improvement_chain(self):
        """
        Initialize the chain for improving code based on review feedback.
        """
        template = """
        You are an expert software developer. Your task is to improve the following code
        based on the review feedback:
        
        Original code:
        ```{language}
        {code}
        ```
        
        Review issues:
        {issues}
        
        Review suggestions:
        {suggestions}
        
        Task context:
        {task_description}
        
        Please provide an improved version of the code that addresses the review feedback.
        """
        
        self.code_improvement_chain = create_text_output_chain(
            self.llm,
            template
        )
    
    def generate_code(self, task: TechnicalTask, context: str = "") -> List[CodeSnippet]:
        """
        Generate code based on a technical task.
        
        Args:
            task: Technical task to generate code for
            context: Additional context for code generation
            
        Returns:
            List of generated code snippets
        """
        result = self.code_generation_chain.invoke({
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "context": context
        })
        
        code_snippets = []
        
        for snippet_data in result.code_snippets:
            # Ensure the snippet has an ID
            if "id" not in snippet_data:
                snippet_data["id"] = f"CODE-{uuid.uuid4().hex[:8]}"
                
            # Ensure task_id is set
            snippet_data["task_id"] = task.id
                
            code_snippet = CodeSnippet(**snippet_data)
            code_snippets.append(code_snippet)
        
        return code_snippets
    
    def review_code(self, code_snippet: CodeSnippet, task_description: str) -> CodeReviewOutput:
        """
        Review generated code.
        
        Args:
            code_snippet: Code snippet to review
            task_description: Description of the task the code implements
            
        Returns:
            Review results
        """
        result = self.code_review_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "task_description": task_description
        })
        
        return result
    
    def improve_code(self, code_snippet: CodeSnippet, review_result: CodeReviewOutput, task_description: str) -> CodeSnippet:
        """
        Improve code based on review feedback.
        
        Args:
            code_snippet: Original code snippet
            review_result: Review results
            task_description: Description of the task the code implements
            
        Returns:
            Improved code snippet
        """
        improved_code = self.code_improvement_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "issues": "\n".join(review_result.issues),
            "suggestions": "\n".join(review_result.suggestions),
            "task_description": task_description
        })
        
        # Create a new code snippet with the improved code
        improved_snippet = CodeSnippet(
            id=f"{code_snippet.id}-improved",
            task_id=code_snippet.task_id,
            code=improved_code,
            language=code_snippet.language,
            file_path=code_snippet.file_path,
            description=f"Improved version of {code_snippet.id}"
        )
        
        return improved_snippet
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
                - task: Technical task to generate code for
                - tasks: List of technical tasks to generate code for
                - code_snippet: Code snippet to review/improve
                - workflow_state: Current workflow state
                
        Returns:
            Output data from the agent including:
                - code_snippets: List of generated code snippets
                - review_result: Code review results
                - improved_code: Improved code snippet
                - workflow_state: Updated workflow state
        """
        # Update agent state
        self.update_state(status="working")
        
        # Get workflow state
        workflow_state = inputs.get("workflow_state", {})
        
        # Process based on inputs
        if "task" in inputs:
            # Generate code for a single task
            task = inputs["task"]
            if isinstance(task, dict):
                task = TechnicalTask(**task)
                
            context = inputs.get("context", "")
            code_snippets = self.generate_code(task, context)
            
            # Update workflow state
            if workflow_state:
                workflow_state.code_snippets.extend(code_snippets)
                workflow_state.current_step = "code_generation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "code_snippets": code_snippets,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "tasks" in inputs:
            # Generate code for multiple tasks
            tasks = inputs["tasks"]
            if isinstance(tasks[0], dict):
                tasks = [TechnicalTask(**task) for task in tasks]
                
            all_code_snippets = []
            for task in tasks:
                context = inputs.get("context", "")
                code_snippets = self.generate_code(task, context)
                all_code_snippets.extend(code_snippets)
            
            # Update workflow state
            if workflow_state:
                workflow_state.code_snippets.extend(all_code_snippets)
                workflow_state.current_step = "code_generation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "code_snippets": all_code_snippets,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "code_snippet" in inputs and inputs.get("action") == "review":
            # Review code
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            task_description = inputs.get("task_description", "")
            review_result = self.review_code(code_snippet, task_description)
            
            # Update workflow state
            if workflow_state:
                workflow_state.current_step = "code_review"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "review_result": review_result,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "code_snippet" in inputs and "review_result" in inputs and inputs.get("action") == "improve":
            # Improve code
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            review_result = inputs["review_result"]
            if isinstance(review_result, dict):
                review_result = CodeReviewOutput(**review_result)
                
            task_description = inputs.get("task_description", "")
            improved_code = self.improve_code(code_snippet, review_result, task_description)
            
            # Update workflow state
            if workflow_state:
                workflow_state.code_snippets.append(improved_code)
                workflow_state.current_step = "code_improvement"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "improved_code": improved_code,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        else:
            # Invalid input
            self.update_state(status="error")
            return {
                "error": "Invalid input. Expected 'task', 'tasks', or 'code_snippet' with appropriate action.",
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "error"
            }
