"""
Main workflow orchestration for the Autonomous Software Development Agent.
"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph

from autonomous_dev_agent.src.agents.base_agent import BaseAgent, create_agent_workflow
from autonomous_dev_agent.src.models.base_models import WorkflowState


class DevelopmentWorkflow:
    """
    Main workflow orchestration for the autonomous software development process.
    """
    
    def __init__(self, workflow_id: str):
        """
        Initialize the development workflow.
        
        Args:
            workflow_id: Unique identifier for this workflow
        """
        self.workflow_id = workflow_id
        self.agents = []
        self.workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status="in_progress",
            current_step="initialization"
        )
        self.graph = None
    
    def add_agent(self, agent: BaseAgent) -> None:
        """
        Add an agent to the workflow.
        
        Args:
            agent: The agent to add
        """
        self.agents.append(agent)
        self.workflow_state.agent_states[agent.agent_id] = agent.get_state()
    
    def build_graph(self) -> StateGraph:
        """
        Build the workflow graph connecting all agents.
        
        Returns:
            A StateGraph representing the workflow
        """
        self.graph = create_agent_workflow(self.agents, self.workflow_id)
        return self.graph
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the workflow with the given inputs.
        
        Args:
            inputs: Input data to start the workflow
            
        Returns:
            The final output of the workflow
        """
        if self.graph is None:
            self.build_graph()
        
        # Compile the graph
        compiled_graph = self.graph.compile()
        
        # Add workflow state to inputs
        inputs["workflow_state"] = self.workflow_state
        
        # Run the workflow
        result = compiled_graph.invoke(inputs)
        
        # Update workflow state from result
        if "workflow_state" in result:
            self.workflow_state = result["workflow_state"]
        
        return result
    
    def get_state(self) -> WorkflowState:
        """
        Get the current state of the workflow.
        
        Returns:
            The workflow's current state
        """
        return self.workflow_state
