"""
Planning agent for breaking down requirements into technical tasks.
"""
from typing import Dict, Any, List, Optional
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import Requirement, TechnicalTask
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain
from autonomous_dev_agent.src.config.config import settings


class RequirementAnalysisOutput(BaseModel):
    """
    Output schema for requirement analysis.
    """
    requirements: List[Dict[str, Any]] = Field(
        description="List of identified requirements from the input"
    )


class TaskBreakdownOutput(BaseModel):
    """
    Output schema for task breakdown.
    """
    tasks: List[Dict[str, Any]] = Field(
        description="List of technical tasks derived from the requirements"
    )


class PlanningAgent(BaseAgent):
    """
    Agent responsible for analyzing requirements and breaking them down into technical tasks.
    """
    
    def __init__(self, agent_id: str = "planning_agent"):
        """
        Initialize the planning agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        super().__init__(agent_id, "planning")
        self.llm = get_openai_llm(model=settings.PLANNING_LLM_MODEL)
        
        # Initialize chains
        self._init_requirement_analysis_chain()
        self._init_task_breakdown_chain()
    
    def _init_requirement_analysis_chain(self):
        """
        Initialize the chain for analyzing natural language requirements.
        """
        template = """
        You are an expert software requirements analyst. Your task is to analyze the following
        natural language description and extract clear, specific software requirements.
        
        For each requirement:
        1. Assign a unique ID (e.g., REQ-001)
        2. Write a clear, concise description
        3. Assign a priority (high, medium, low)
        4. Add relevant tags
        5. Identify dependencies between requirements if any
        
        Natural language description:
        {description}
        
        Return the requirements in a structured format.
        """
        
        self.requirement_analysis_chain = create_structured_output_chain(
            self.llm,
            template,
            RequirementAnalysisOutput
        )
    
    def _init_task_breakdown_chain(self):
        """
        Initialize the chain for breaking down requirements into technical tasks.
        """
        template = """
        You are an expert software architect and technical lead. Your task is to break down
        the following requirements into specific technical tasks that developers can implement.
        
        For each task:
        1. Assign a unique ID (e.g., TASK-001)
        2. Write a clear, descriptive title
        3. Provide a detailed description including technical approach
        4. Link to the requirement IDs this task fulfills
        5. Estimate complexity (high, medium, low)
        6. Identify dependencies between tasks if any
        
        Requirements:
        {requirements}
        
        Return the technical tasks in a structured format.
        """
        
        self.task_breakdown_chain = create_structured_output_chain(
            self.llm,
            template,
            TaskBreakdownOutput
        )
    
    def analyze_requirements(self, description: str) -> List[Requirement]:
        """
        Analyze natural language description and extract requirements.
        
        Args:
            description: Natural language description of the software
            
        Returns:
            List of extracted requirements
        """
        result = self.requirement_analysis_chain.invoke({"description": description})
        requirements = []
        
        for req_data in result.requirements:
            # Ensure the requirement has an ID
            if "id" not in req_data:
                req_data["id"] = f"REQ-{uuid.uuid4().hex[:8]}"
                
            requirement = Requirement(**req_data)
            requirements.append(requirement)
        
        return requirements
    
    def break_down_tasks(self, requirements: List[Requirement]) -> List[TechnicalTask]:
        """
        Break down requirements into technical tasks.
        
        Args:
            requirements: List of requirements to break down
            
        Returns:
            List of technical tasks
        """
        # Convert requirements to a string representation for the prompt
        req_str = "\n".join([
            f"ID: {req.id}\nDescription: {req.description}\nPriority: {req.priority}\nTags: {', '.join(req.tags)}\n"
            for req in requirements
        ])
        
        result = self.task_breakdown_chain.invoke({"requirements": req_str})
        tasks = []
        
        for task_data in result.tasks:
            # Ensure the task has an ID
            if "id" not in task_data:
                task_data["id"] = f"TASK-{uuid.uuid4().hex[:8]}"
                
            # Convert requirement_ids to a list if it's not already
            if "requirement_ids" in task_data and not isinstance(task_data["requirement_ids"], list):
                task_data["requirement_ids"] = [task_data["requirement_ids"]]
                
            task = TechnicalTask(**task_data)
            tasks.append(task)
        
        return tasks
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
                - description: Natural language description (for requirement analysis)
                - requirements: List of requirements (for task breakdown)
                - workflow_state: Current workflow state
                
        Returns:
            Output data from the agent including:
                - requirements: List of requirements (if analyzed)
                - tasks: List of technical tasks (if broken down)
                - workflow_state: Updated workflow state
        """
        # Update agent state
        self.update_state(status="working")
        
        # Get workflow state
        workflow_state = inputs.get("workflow_state", {})
        
        # Process based on inputs
        if "description" in inputs:
            # Analyze requirements from description
            requirements = self.analyze_requirements(inputs["description"])
            
            # Break down requirements into tasks
            tasks = self.break_down_tasks(requirements)
            
            # Update workflow state
            if workflow_state:
                workflow_state.requirements = requirements
                workflow_state.technical_tasks = tasks
                workflow_state.current_step = "requirement_analysis"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "requirements": requirements,
                "tasks": tasks,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        elif "requirements" in inputs:
            # Break down requirements into tasks
            requirements = inputs["requirements"]
            if isinstance(requirements[0], dict):
                requirements = [Requirement(**req) for req in requirements]
                
            tasks = self.break_down_tasks(requirements)
            
            # Update workflow state
            if workflow_state:
                workflow_state.technical_tasks = tasks
                workflow_state.current_step = "task_breakdown"
            
            # Update agent state
            self.update_state(status="idle")
            
            return {
                "tasks": tasks,
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "completed"
            }
            
        else:
            # Invalid input
            self.update_state(status="error")
            return {
                "error": "Invalid input. Expected 'description' or 'requirements'.",
                "workflow_state": workflow_state,
                "current_agent_id": self.agent_id,
                "status": "error"
            }
