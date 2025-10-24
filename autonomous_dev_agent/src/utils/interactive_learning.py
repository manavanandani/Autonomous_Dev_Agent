"""
Interactive learning mechanism for agent improvement based on user feedback.
"""
from typing import Dict, Any, List, Optional, Union
import uuid
import json
import os
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from autonomous_dev_agent.src.models.base_models import Feedback
from autonomous_dev_agent.src.utils.llm_utils import get_openai_llm, create_structured_output_chain, create_text_output_chain
from autonomous_dev_agent.src.config.config import settings


class FeedbackAnalysisOutput(BaseModel):
    """
    Output schema for feedback analysis.
    """
    strengths: List[str] = Field(
        description="Identified strengths in the agent's output"
    )
    weaknesses: List[str] = Field(
        description="Identified weaknesses in the agent's output"
    )
    improvement_areas: List[Dict[str, str]] = Field(
        description="Specific areas for improvement with suggestions"
    )
    priority_score: float = Field(
        description="Priority score for implementing the feedback (0.0 to 1.0)"
    )


class LearningRecord(BaseModel):
    """
    Record of learning from feedback.
    """
    id: str
    feedback_id: str
    agent_id: str
    learning_points: List[str]
    implementation_status: str = "pending"  # pending, implemented, rejected
    created_at: str


class FeedbackManager:
    """
    Manager for collecting and processing user feedback.
    """
    
    def __init__(self, feedback_dir: str = None):
        """
        Initialize the feedback manager.
        
        Args:
            feedback_dir: Directory to store feedback data
        """
        self.feedback_dir = feedback_dir or os.path.join(os.getcwd(), "feedback_data")
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        self.feedback_file = os.path.join(self.feedback_dir, "feedback.json")
        self.learning_file = os.path.join(self.feedback_dir, "learning.json")
        
        # Initialize files if they don't exist
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, "w") as f:
                json.dump([], f)
        
        if not os.path.exists(self.learning_file):
            with open(self.learning_file, "w") as f:
                json.dump([], f)
        
        # Initialize LLM and chains
        self.llm = get_openai_llm()
        self._init_feedback_analysis_chain()
        self._init_learning_generation_chain()
    
    def _init_feedback_analysis_chain(self):
        """
        Initialize the chain for analyzing feedback.
        """
        template = """
        You are an expert in AI agent improvement. Your task is to analyze the following user feedback
        about an AI agent's output and identify strengths, weaknesses, and areas for improvement.
        
        Agent output:
        {agent_output}
        
        User feedback:
        {feedback_content}
        
        Please analyze the feedback and provide:
        1. Strengths identified in the agent's output
        2. Weaknesses identified in the agent's output
        3. Specific areas for improvement with concrete suggestions
        4. A priority score (0.0 to 1.0) indicating how important it is to implement this feedback
        
        Be objective and focus on actionable insights that can help improve the agent.
        """
        
        self.feedback_analysis_chain = create_structured_output_chain(
            self.llm,
            template,
            FeedbackAnalysisOutput
        )
    
    def _init_learning_generation_chain(self):
        """
        Initialize the chain for generating learning points from feedback.
        """
        template = """
        You are an expert in AI agent improvement. Your task is to generate specific learning points
        based on the analyzed feedback that can be used to improve the agent.
        
        Feedback analysis:
        Strengths: {strengths}
        Weaknesses: {weaknesses}
        Improvement areas: {improvement_areas}
        Priority score: {priority_score}
        
        Agent type: {agent_type}
        
        Please generate 3-5 specific, actionable learning points that can be implemented to improve
        the agent based on this feedback. Each learning point should be concrete and directly
        applicable to the agent's functionality.
        
        Format each learning point as a separate item in a list.
        """
        
        self.learning_generation_chain = create_text_output_chain(
            self.llm,
            template
        )
    
    def collect_feedback(self, content: str, target_id: str, target_type: str, rating: Optional[float] = None) -> Feedback:
        """
        Collect and store user feedback.
        
        Args:
            content: Feedback content
            target_id: ID of the entity receiving feedback
            target_type: Type of entity (code, test, documentation, etc.)
            rating: Optional numerical rating
            
        Returns:
            Created feedback object
        """
        feedback_id = f"FEEDBACK-{uuid.uuid4().hex[:8]}"
        
        feedback = Feedback(
            id=feedback_id,
            content=content,
            target_id=target_id,
            target_type=target_type,
            rating=rating
        )
        
        # Load existing feedback
        with open(self.feedback_file, "r") as f:
            feedbacks = json.load(f)
        
        # Add new feedback
        feedbacks.append(feedback.dict())
        
        # Save updated feedback
        with open(self.feedback_file, "w") as f:
            json.dump(feedbacks, f, indent=2)
        
        return feedback
    
    def analyze_feedback(self, feedback: Union[Feedback, str], agent_output: str) -> FeedbackAnalysisOutput:
        """
        Analyze feedback to identify strengths, weaknesses, and areas for improvement.
        
        Args:
            feedback: Feedback object or feedback ID
            agent_output: Output that received the feedback
            
        Returns:
            Analysis of the feedback
        """
        # Get feedback object if ID is provided
        if isinstance(feedback, str):
            feedback_obj = self.get_feedback(feedback)
            if not feedback_obj:
                raise ValueError(f"Feedback with ID {feedback} not found")
        else:
            feedback_obj = feedback
        
        # Analyze feedback
        result = self.feedback_analysis_chain.invoke({
            "agent_output": agent_output,
            "feedback_content": feedback_obj.content
        })
        
        return result
    
    def generate_learning(self, feedback_analysis: FeedbackAnalysisOutput, agent_id: str, agent_type: str, feedback_id: str) -> LearningRecord:
        """
        Generate learning points from feedback analysis.
        
        Args:
            feedback_analysis: Analysis of the feedback
            agent_id: ID of the agent
            agent_type: Type of agent
            feedback_id: ID of the feedback
            
        Returns:
            Learning record
        """
        # Format improvement areas for the prompt
        improvement_areas_str = "\n".join([
            f"- {area.get('area', 'Unknown')}: {area.get('suggestion', '')}"
            for area in feedback_analysis.improvement_areas
        ])
        
        # Generate learning points
        learning_points_text = self.learning_generation_chain.invoke({
            "strengths": "\n".join([f"- {s}" for s in feedback_analysis.strengths]),
            "weaknesses": "\n".join([f"- {w}" for w in feedback_analysis.weaknesses]),
            "improvement_areas": improvement_areas_str,
            "priority_score": feedback_analysis.priority_score,
            "agent_type": agent_type
        })
        
        # Parse learning points
        learning_points = [
            point.strip().lstrip("- ").lstrip("* ")
            for point in learning_points_text.split("\n")
            if point.strip() and not point.strip().startswith("#")
        ]
        
        # Create learning record
        learning_id = f"LEARNING-{uuid.uuid4().hex[:8]}"
        
        learning_record = LearningRecord(
            id=learning_id,
            feedback_id=feedback_id,
            agent_id=agent_id,
            learning_points=learning_points,
            implementation_status="pending",
            created_at=datetime.now().isoformat()
        )
        
        # Load existing learning records
        with open(self.learning_file, "r") as f:
            learning_records = json.load(f)
        
        # Add new learning record
        learning_records.append(learning_record.dict())
        
        # Save updated learning records
        with open(self.learning_file, "w") as f:
            json.dump(learning_records, f, indent=2)
        
        return learning_record
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id: ID of the feedback
            
        Returns:
            Feedback object if found, None otherwise
        """
        # Load existing feedback
        with open(self.feedback_file, "r") as f:
            feedbacks = json.load(f)
        
        # Find feedback by ID
        for feedback_data in feedbacks:
            if feedback_data.get("id") == feedback_id:
                return Feedback(**feedback_data)
        
        return None
    
    def get_learning(self, learning_id: str) -> Optional[LearningRecord]:
        """
        Get learning record by ID.
        
        Args:
            learning_id: ID of the learning record
            
        Returns:
            Learning record if found, None otherwise
        """
        # Load existing learning records
        with open(self.learning_file, "r") as f:
            learning_records = json.load(f)
        
        # Find learning record by ID
        for learning_data in learning_records:
            if learning_data.get("id") == learning_id:
                return LearningRecord(**learning_data)
        
        return None
    
    def get_learning_for_agent(self, agent_id: str) -> List[LearningRecord]:
        """
        Get all learning records for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of learning records
        """
        # Load existing learning records
        with open(self.learning_file, "r") as f:
            learning_records = json.load(f)
        
        # Find learning records for agent
        agent_learning = []
        for learning_data in learning_records:
            if learning_data.get("agent_id") == agent_id:
                agent_learning.append(LearningRecord(**learning_data))
        
        return agent_learning
    
    def update_learning_status(self, learning_id: str, status: str) -> Optional[LearningRecord]:
        """
        Update the implementation status of a learning record.
        
        Args:
            learning_id: ID of the learning record
            status: New status (pending, implemented, rejected)
            
        Returns:
            Updated learning record if found, None otherwise
        """
        # Load existing learning records
        with open(self.learning_file, "r") as f:
            learning_records = json.load(f)
        
        # Find and update learning record
        updated_record = None
        for i, learning_data in enumerate(learning_records):
            if learning_data.get("id") == learning_id:
                learning_records[i]["implementation_status"] = status
                updated_record = LearningRecord(**learning_records[i])
                break
        
        if updated_record:
            # Save updated learning records
            with open(self.learning_file, "w") as f:
                json.dump(learning_records, f, indent=2)
        
        return updated_record


class InteractiveLearningSystem:
    """
    System for interactive learning and agent improvement based on user feedback.
    """
    
    def __init__(self):
        """
        Initialize the interactive learning system.
        """
        self.feedback_manager = FeedbackManager()
        self.llm = get_openai_llm()
        self._init_prompt_improvement_chain()
    
    def _init_prompt_improvement_chain(self):
        """
        Initialize the chain for improving agent prompts based on learning.
        """
        template = """
        You are an expert in AI prompt engineering. Your task is to improve the following prompt
        based on the learning points derived from user feedback.
        
        Original prompt:
        {original_prompt}
        
        Learning points:
        {learning_points}
        
        Please provide an improved version of the prompt that incorporates the learning points.
        The improved prompt should maintain the original structure and purpose but address the
        issues identified in the learning points.
        
        Return only the improved prompt text without any additional explanation.
        """
        
        self.prompt_improvement_chain = create_text_output_chain(
            self.llm,
            template
        )
    
    def collect_and_process_feedback(self, feedback_content: str, target_id: str, target_type: str, agent_id: str, agent_type: str, agent_output: str, rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Collect feedback and process it to generate learning.
        
        Args:
            feedback_content: Feedback content
            target_id: ID of the entity receiving feedback
            target_type: Type of entity
            agent_id: ID of the agent
            agent_type: Type of agent
            agent_output: Output that received the feedback
            rating: Optional numerical rating
            
        Returns:
            Dictionary with feedback and learning information
        """
        # Collect feedback
        feedback = self.feedback_manager.collect_feedback(
            content=feedback_content,
            target_id=target_id,
            target_type=target_type,
            rating=rating
        )
        
        # Analyze feedback
        analysis = self.feedback_manager.analyze_feedback(
            feedback=feedback,
            agent_output=agent_output
        )
        
        # Generate learning
        learning = self.feedback_manager.generate_learning(
            feedback_analysis=analysis,
            agent_id=agent_id,
            agent_type=agent_type,
            feedback_id=feedback.id
        )
        
        return {
            "feedback": feedback,
            "analysis": analysis,
            "learning": learning
        }
    
    def improve_agent_prompt(self, original_prompt: str, learning_points: List[str]) -> str:
        """
        Improve an agent's prompt based on learning points.
        
        Args:
            original_prompt: Original prompt text
            learning_points: List of learning points
            
        Returns:
            Improved prompt text
        """
        # Format learning points for the prompt
        learning_points_str = "\n".join([f"- {point}" for point in learning_points])
        
        # Generate improved prompt
        improved_prompt = self.prompt_improvement_chain.invoke({
            "original_prompt": original_prompt,
            "learning_points": learning_points_str
        })
        
        return improved_prompt
    
    def apply_learning_to_agent(self, agent_id: str, agent_type: str, original_prompts: Dict[str, str]) -> Dict[str, str]:
        """
        Apply learning to improve an agent's prompts.
        
        Args:
            agent_id: ID of the agent
            agent_type: Type of agent
            original_prompts: Dictionary mapping prompt names to prompt texts
            
        Returns:
            Dictionary mapping prompt names to improved prompt texts
        """
        # Get learning for agent
        learning_records = self.feedback_manager.get_learning_for_agent(agent_id)
        
        # Filter for pending learning
        pending_learning = [
            record for record in learning_records
            if record.implementation_status == "pending"
        ]
        
        if not pending_learning:
            return original_prompts
        
        # Collect all learning points
        all_learning_points = []
        for record in pending_learning:
            all_learning_points.extend(record.learning_points)
        
        # Improve each prompt
        improved_prompts = {}
        for prompt_name, prompt_text in original_prompts.items():
            improved_prompts[prompt_name] = self.improve_agent_prompt(
                original_prompt=prompt_text,
                learning_points=all_learning_points
            )
        
        # Update learning status
        for record in pending_learning:
            self.feedback_manager.update_learning_status(
                learning_id=record.id,
                status="implemented"
            )
        
        return improved_prompts
