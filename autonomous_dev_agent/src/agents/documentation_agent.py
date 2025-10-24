"""
Documentation agent for creating code and user documentation.
"""
from typing import Dict, Any, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import CodeSnippet, Documentation
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain, create_text_output_chain
from autonomous_dev_agent.src.config.config import settings


class CodeDocumentationOutput(BaseModel):
    """
    Output schema for code documentation.
    """
    documentation: Dict[str, Any] = Field(
        description="Generated documentation for the code"
    )


class UserDocumentationOutput(BaseModel):
    """
    Output schema for user documentation.
    """
    documentation: Dict[str, Any] = Field(
        description="Generated user documentation"
    )


class DocumentationAgent(BaseAgent):
    """
    Agent responsible for creating documentation for code and features.
    """
    
    def __init__(self, agent_id: str = "documentation_agent"):
        """
        Initialize the documentation agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        super().__init__(agent_id, "documentation")
        self.llm = get_openai_llm(model=settings.DOCUMENTATION_LLM_MODEL)
        
        # Initialize chains
        self._init_code_documentation_chain()
        self._init_user_documentation_chain()
        self._init_api_documentation_chain()
    
    def _init_code_documentation_chain(self):
        """
        Initialize the chain for generating code documentation.
        """
        template = """
        You are an expert technical writer specializing in code documentation. Your task is to create
        comprehensive documentation for the following code:
        
        ```{language}
        {code}
        ```
        
        Code description: {description}
        
        Please provide:
        1. A clear title for the documentation
        2. A detailed explanation of what the code does
        3. Documentation for each function, class, and method
        4. Explanation of key algorithms and data structures
        5. Usage examples
        6. Any dependencies or requirements
        
        The documentation should be thorough, technically accurate, and follow best practices
        for the specific programming language.
        
        Return the documentation in a structured format.
        """
        
        self.code_documentation_chain = create_structured_output_chain(
            self.llm,
            template,
            CodeDocumentationOutput
        )
    
    def _init_user_documentation_chain(self):
        """
        Initialize the chain for generating user documentation.
        """
        template = """
        You are an expert technical writer specializing in user documentation. Your task is to create
        user-friendly documentation for the following feature:
        
        Feature name: {feature_name}
        Feature description: {feature_description}
        
        Code snippets:
        {code_snippets}
        
        Please provide:
        1. A clear title for the documentation
        2. An overview of the feature and its purpose
        3. Step-by-step instructions for using the feature
        4. Examples of common use cases
        5. Troubleshooting tips
        6. FAQ section
        
        The documentation should be user-friendly, clear, and accessible to non-technical users
        while still providing all necessary information.
        
        Return the documentation in a structured format.
        """
        
        self.user_documentation_chain = create_structured_output_chain(
            self.llm,
            template,
            UserDocumentationOutput
        )
    
    def _init_api_documentation_chain(self):
        """
        Initialize the chain for generating API documentation.
        """
        template = """
        You are an expert technical writer specializing in API documentation. Your task is to create
        comprehensive API documentation for the following code:
        
        ```{language}
        {code}
        ```
        
        API description: {description}
        
        Please provide:
        1. A clear title for the API documentation
        2. An overview of the API and its purpose
        3. Detailed documentation for each endpoint/function
           - Parameters (name, type, description, required/optional)
           - Return values (type, description)
           - Error codes and handling
        4. Authentication requirements
        5. Rate limiting information
        6. Example requests and responses
        
        The documentation should follow industry standards for API documentation and be
        accessible to developers who will integrate with this API.
        
        Return the documentation in a structured format.
        """
        
        self.api_documentation_chain = create_structured_output_chain(
            self.llm,
            template,
            CodeDocumentationOutput
        )
    
    def generate_code_documentation(self, code_snippet: CodeSnippet) -> Documentation:
        """
        Generate documentation for a code snippet.
        
        Args:
            code_snippet: Code snippet to document
            
        Returns:
            Generated documentation
        """
        result = self.code_documentation_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "description": code_snippet.description
        })
        
        doc_data = result.documentation
        
        # Ensure the documentation has an ID
        if "id" not in doc_data:
            doc_data["id"] = f"DOC-CODE-{uuid.uuid4().hex[:8]}"
            
        # Ensure code_snippet_ids is set
        if "code_snippet_ids" not in doc_data:
            doc_data["code_snippet_ids"] = [code_snippet.id]
            
        # Set doc_type if not present
        if "doc_type" not in doc_data:
            doc_data["doc_type"] = "technical"
            
        documentation = Documentation(**doc_data)
        return documentation
    
    def generate_user_documentation(self, feature_name: str, feature_description: str, code_snippets: List[CodeSnippet]) -> Documentation:
        """
        Generate user documentation for a feature.
        
        Args:
            feature_name: Name of the feature
            feature_description: Description of the feature
            code_snippets: List of code snippets related to the feature
            
        Returns:
            Generated documentation
        """
        # Format code snippets for the prompt
        code_snippets_str = ""
        for snippet in code_snippets:
            code_snippets_str += f"File: {snippet.file_path or 'Unknown'}\n"
            code_snippets_str += f"Description: {snippet.description}\n"
            code_snippets_str += f"```{snippet.language}\n{snippet.code}\n```\n\n"
        
        result = self.user_documentation_chain.invoke({
            "feature_name": feature_name,
            "feature_description": feature_description,
            "code_snippets": code_snippets_str
        })
        
        doc_data = result.documentation
        
        # Ensure the documentation has an ID
        if "id" not in doc_data:
            doc_data["id"] = f"DOC-USER-{uuid.uuid4().hex[:8]}"
            
        # Ensure code_snippet_ids is set
        if "code_snippet_ids" not in doc_data:
            doc_data["code_snippet_ids"] = [snippet.id for snippet in code_snippets]
            
        # Set doc_type if not present
        if "doc_type" not in doc_data:
            doc_data["doc_type"] = "user"
            
        documentation = Documentation(**doc_data)
        return documentation
    
    def generate_api_documentation(self, code_snippet: CodeSnippet, description: str) -> Documentation:
        """
        Generate API documentation for a code snippet.
        
        Args:
            code_snippet: Code snippet to document
            description: Description of the API
            
        Returns:
            Generated documentation
        """
        result = self.api_documentation_chain.invoke({
            "language": code_snippet.language,
            "code": code_snippet.code,
            "description": description
        })
        
        doc_data = result.documentation
        
        # Ensure the documentation has an ID
        if "id" not in doc_data:
            doc_data["id"] = f"DOC-API-{uuid.uuid4().hex[:8]}"
            
        # Ensure code_snippet_ids is set
        if "code_snippet_ids" not in doc_data:
            doc_data["code_snippet_ids"] = [code_snippet.id]
            
        # Set doc_type if not present
        if "doc_type" not in doc_data:
            doc_data["doc_type"] = "api"
            
        documentation = Documentation(**doc_data)
        return documentation
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
                - code_snippet: Code snippet to document
                - feature_name: Name of the feature for user documentation
                - feature_description: Description of the feature for user documentation
                - code_snippets: List of code snippets for user documentation
                - api_description: Description of the API for API documentation
                - doc_type: Type of documentation to generate (technical, user, api)
                - workflow_state: Current workflow state
                
        Returns:
            Output data from the agent including:
                - documentation: Generated documentation
                - workflow_state: Updated workflow state
        """
        # Update agent state
        self.update_state(status="working")
        
        # Get workflow state
        workflow_state = inputs.get("workflow_state", {})
        
        # Process based on inputs
        doc_type = inputs.get("doc_type", "technical")
        
        if doc_type == "technical" and "code_snippet" in inputs:
            # Generate technical documentation for a code snippet
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            documentation = self.generate_code_documentation(code_snippet)
            
            # Update workflow state
            if workflow_state:
                workflow_state.documentation.append(documentation)
                workflow_state.current_step = "code_documentation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "documentation": documentation,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif doc_type == "user" and "feature_name" in inputs and "feature_description" in inputs and "code_snippets" in inputs:
            # Generate user documentation for a feature
            feature_name = inputs["feature_name"]
            feature_description = inputs["feature_description"]
            
            code_snippets = inputs["code_snippets"]
            if isinstance(code_snippets[0], dict):
                code_snippets = [CodeSnippet(**snippet) for snippet in code_snippets]
                
            documentation = self.generate_user_documentation(feature_name, feature_description, code_snippets)
            
            # Update workflow state
            if workflow_state:
                workflow_state.documentation.append(documentation)
                workflow_state.current_step = "user_documentation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "documentation": documentation,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif doc_type == "api" and "code_snippet" in inputs and "api_description" in inputs:
            # Generate API documentation for a code snippet
            code_snippet = inputs["code_snippet"]
            if isinstance(code_snippet, dict):
                code_snippet = CodeSnippet(**code_snippet)
                
            api_description = inputs["api_description"]
            
            documentation = self.generate_api_documentation(code_snippet, api_description)
            
            # Update workflow state
            if workflow_state:
                workflow_state.documentation.append(documentation)
                workflow_state.current_step = "api_documentation"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "documentation": documentation,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        else:
            # Invalid input
            self.update_state(status="error")
            return {
                "error": "Invalid input. Expected 'code_snippet' for technical documentation, 'feature_name', 'feature_description', and 'code_snippets' for user documentation, or 'code_snippet' and 'api_description' for API documentation.",
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "error"
            }
