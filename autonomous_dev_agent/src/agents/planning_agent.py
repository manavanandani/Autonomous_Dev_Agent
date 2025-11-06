"""
Enhanced Planning Agent - Generates detailed execution plans before code generation
"""
from typing import Dict, Any, List, Optional
import uuid
import json
import os
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from autonomous_dev_agent.src.agents.base_agent import BaseAgent
from autonomous_dev_agent.src.models.base_models import Requirement, TechnicalTask
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain
from autonomous_dev_agent.src.config.config import settings


class PlanStep(BaseModel):
    """Individual step in the execution plan"""
    step_number: int = Field(..., description="Sequential step number")
    title: str = Field(..., description="Short descriptive title for the step")
    description: str = Field(..., description="Detailed description of what needs to be done")
    estimated_time: str = Field(..., description="Estimated time to complete this step")
    dependencies: List[int] = Field(default_factory=list, description="Step numbers this step depends on")
    files_to_create: List[str] = Field(default_factory=list, description="Files that will be created in this step")
    files_to_modify: List[str] = Field(default_factory=list, description="Files that will be modified in this step")
    key_functions: List[str] = Field(default_factory=list, description="Key functions or components to implement")
    complexity_level: str = Field(default="medium", description="Complexity level: low, medium, high")


class ExecutionPlan(BaseModel):
    """Complete execution plan for a requirement"""
    requirement: str = Field(..., description="Original requirement description")
    summary: str = Field(..., description="High-level summary of the solution approach")
    total_estimated_time: str = Field(..., description="Total estimated time for complete implementation")
    architecture_overview: str = Field(..., description="High-level architecture and design patterns")
    technology_stack: List[str] = Field(default_factory=list, description="Technologies, libraries, and frameworks needed")
    steps: List[PlanStep] = Field(default_factory=list, description="Detailed implementation steps")
    risk_assessment: str = Field(..., description="Potential challenges and mitigation strategies")
    success_criteria: List[str] = Field(default_factory=list, description="Criteria to measure successful implementation")
    project_structure: List[str] = Field(default_factory=list, description="Recommended file/folder structure")
    testing_strategy: str = Field(..., description="Approach for testing the implementation")


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
    
    async def create_execution_plan(self, requirement: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create a detailed execution plan for the given requirement
        
        Args:
            requirement: Natural language requirement description
            context: Optional context information (existing codebase, constraints, etc.)
            
        Returns:
            ExecutionPlan: Detailed plan with steps, timeline, and architecture
        """
        try:
            self.logger.info(f"Creating execution plan for requirement: {requirement[:100]}...")
            
            # Check if we're in dry run mode
            if os.getenv("DRY_RUN", "false").lower() == "true":
                self.logger.info("DRY RUN: Creating mock execution plan")
                return self._create_mock_plan(requirement)
            
            # Build the planning prompt
            planning_prompt = self._build_planning_prompt(requirement, context)
            
            # Create planning chain
            planning_chain = create_structured_output_chain(
                self.llm,
                planning_prompt,
                ExecutionPlan
            )
            
            # Generate the execution plan
            execution_plan = planning_chain.invoke({
                "requirement": requirement,
                "context": context or {}
            })
            
            self.logger.info(f"Successfully created execution plan with {len(execution_plan.steps)} steps")
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"Error creating execution plan: {str(e)}")
            # Return a fallback plan
            return self._create_fallback_plan(requirement)
    
    def _build_planning_prompt(self, requirement: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the planning prompt for the LLM"""
        prompt = """
        You are a senior software architect creating a detailed execution plan.
        
        REQUIREMENT: {requirement}
        
        Create a comprehensive execution plan with:
        1. Architecture overview and design patterns
        2. Technology stack recommendations  
        3. Step-by-step implementation plan
        4. Risk assessment and mitigation
        5. Success criteria and testing strategy
        
        Provide realistic time estimates and consider dependencies between steps.
        Focus on maintainable, scalable solutions with proper testing.
        """
        
        return prompt
    
    def _create_mock_plan(self, requirement: str) -> ExecutionPlan:
        """Create a detailed mock plan for development/testing"""
        return ExecutionPlan(
            requirement=requirement,
            summary=f"Comprehensive implementation plan for: {requirement[:50]}...",
            total_estimated_time="3-5 hours",
            architecture_overview="Modular design with separation of concerns. Clean architecture pattern with distinct layers for presentation, business logic, and data access.",
            technology_stack=["Python 3.9+", "FastAPI", "Pydantic", "Pytest", "Black", "Mypy"],
            steps=[
                PlanStep(
                    step_number=1,
                    title="Project Structure Setup",
                    description="Create the basic project structure with proper organization of modules and configuration files.",
                    estimated_time="30 minutes",
                    dependencies=[],
                    files_to_create=["src/__init__.py", "src/main.py", "config.py", "requirements.txt", "README.md"],
                    key_functions=["setup_project_structure", "initialize_config"],
                    complexity_level="low"
                ),
                PlanStep(
                    step_number=2,
                    title="Core Logic Implementation", 
                    description="Implement the main business logic and core functionality as specified in requirements.",
                    estimated_time="2 hours",
                    dependencies=[1],
                    files_to_create=["src/core.py", "src/models.py", "src/utils.py"],
                    key_functions=["process_request", "validate_input", "handle_business_logic"],
                    complexity_level="medium"
                ),
                PlanStep(
                    step_number=3,
                    title="API Interface Development",
                    description="Create API endpoints with proper validation, error handling, and documentation.",
                    estimated_time="1.5 hours", 
                    dependencies=[2],
                    files_to_create=["src/api.py", "src/schemas.py"],
                    files_to_modify=["src/main.py"],
                    key_functions=["create_endpoints", "setup_middleware", "handle_errors"],
                    complexity_level="medium"
                ),
                PlanStep(
                    step_number=4,
                    title="Testing Implementation",
                    description="Create comprehensive unit tests and integration tests with proper fixtures.",
                    estimated_time="1 hour",
                    dependencies=[2, 3],
                    files_to_create=["tests/__init__.py", "tests/test_core.py", "tests/test_api.py"],
                    key_functions=["test_core_functionality", "test_api_endpoints", "setup_test_fixtures"],
                    complexity_level="medium"
                ),
                PlanStep(
                    step_number=5,
                    title="Documentation and Finalization",
                    description="Complete documentation, add usage examples, and perform final code review.",
                    estimated_time="45 minutes",
                    dependencies=[4],
                    files_to_modify=["README.md"],
                    files_to_create=["docs/api.md", "examples/usage.py"],
                    key_functions=["generate_docs", "create_examples", "final_validation"],
                    complexity_level="low"
                )
            ],
            risk_assessment="Low to medium risk project. Main challenges: proper error handling, performance optimization, external dependencies. Mitigation: thorough testing, performance profiling, fallback mechanisms.",
            success_criteria=[
                "All core functionality implemented and tested",
                "API endpoints respond correctly with proper status codes",
                "Unit test coverage above 85%",
                "Documentation is complete and accurate",
                "Code passes linting and type checking"
            ],
            project_structure=[
                "src/",
                "├── __init__.py",
                "├── main.py", 
                "├── core.py",
                "├── models.py",
                "├── utils.py",
                "├── api.py",
                "└── schemas.py",
                "tests/",
                "├── __init__.py",
                "├── test_core.py",
                "└── test_api.py",
                "config.py",
                "requirements.txt", 
                "README.md"
            ],
            testing_strategy="Comprehensive testing with unit tests for core logic, integration tests for API endpoints, and end-to-end tests for critical workflows. Use pytest with fixtures and mocking."
        )
    
    def _create_fallback_plan(self, requirement: str) -> ExecutionPlan:
        """Create a basic fallback plan if all else fails"""
        return ExecutionPlan(
            requirement=requirement,
            summary="Basic implementation approach (fallback mode)",
            total_estimated_time="2-4 hours",
            architecture_overview="Standard modular approach with separation of concerns",
            technology_stack=["Python", "Standard Libraries"],
            steps=[
                PlanStep(
                    step_number=1,
                    title="Analyze Requirements",
                    description="Break down the requirement into specific implementation tasks",
                    estimated_time="30 minutes",
                    files_to_create=["analysis.md"],
                    complexity_level="low"
                ),
                PlanStep(
                    step_number=2,
                    title="Implement Core Functionality", 
                    description="Write the main implementation code",
                    estimated_time="2 hours",
                    dependencies=[1],
                    files_to_create=["main.py"],
                    key_functions=["main", "process"],
                    complexity_level="medium"
                )
            ],
            risk_assessment="Low risk - standard implementation pattern",
            success_criteria=["Code passes all tests", "Requirements are fully implemented"],
            project_structure=["main.py", "README.md"],
            testing_strategy="Unit testing with standard assertions"
        )
    
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
