"""
Base agent class for the Autonomous Software Development Agent.
"""
from typing import Dict, Any, List, Optional
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

from autonomous_dev_agent.src.models.base_models import AgentState
from autonomous_dev_agent.src.config.config import settings


class BaseAgent:
    """
    Base class for all agents in the system.
    """
    
    def __init__(self, agent_id: str, agent_type: str):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type of agent (planning, coding, testing, etc.)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            status="idle"
        )
    
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inputs and return outputs.
        
        Args:
            inputs: Input data for the agent to process
            
        Returns:
            Output data from the agent
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def update_state(self, **kwargs) -> None:
        """
        Update the agent's state.
        
        Args:
            **kwargs: Key-value pairs to update in the state
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def get_state(self) -> AgentState:
        """
        Get the current state of the agent.
        
        Returns:
            The agent's current state
        """
        return self.state


def create_agent_workflow(agents: List[BaseAgent], workflow_id: str) -> StateGraph:
    """
    Create a workflow graph connecting multiple agents.
    
    Args:
        agents: List of agent instances to include in the workflow
        workflow_id: Unique identifier for this workflow
        
    Returns:
        A StateGraph representing the workflow
    """
    # Create a mapping of agent IDs to agent instances
    agent_map = {agent.agent_id: agent for agent in agents}
    
    # Define the workflow state
    class WorkflowState(Dict):
        """
        State for the workflow graph.
        """
        pass
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes for each agent
    for agent in agents:
        workflow.add_node(agent.agent_id, agent.process)
    
    # Add the END node
    workflow.add_node("end", lambda x: {"status": "completed"})
    
    # Define conditional routing logic based on your workflow needs
    # This is a simplified example - you'll need to customize this
    def route_based_on_status(state):
        """
        Route to the next agent based on the current state.
        """
        # Extract current_agent_id from the state
        current_agent_id = state.get("current_agent_id")
        
        # Check if there's an error and we should stop
        if "error" in state:
            return "end"
        
        # Route based on current agent
        if current_agent_id == "planning_agent":
            return "coding_agent"
        elif current_agent_id == "coding_agent":
            return "testing_agent"
        elif current_agent_id == "testing_agent":
            return "documentation_agent"
        elif current_agent_id == "debugging_agent":
            return "testing_agent"
        elif current_agent_id == "documentation_agent":
            return "end"
        else:
            # Default to the first agent if no routing is defined
            return agents[0].agent_id
    
    # Add edges between nodes
    for agent in agents:
        workflow.add_conditional_edges(
            agent.agent_id,
            route_based_on_status
        )
    
    # Set the entry point
    workflow.set_entry_point(agents[0].agent_id)
    
    return workflow
