"""
Configuration settings for the Autonomous Software Development Agent.
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model settings
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    CODE_LLM_MODEL: str = "gpt-4o"
    PLANNING_LLM_MODEL: str = "gpt-4o"
    TESTING_LLM_MODEL: str = "gpt-4o"
    DEBUGGING_LLM_MODEL: str = "gpt-4o"
    DOCUMENTATION_LLM_MODEL: str = "gpt-4o"
    
    # GitHub/GitLab settings
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "")
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 4096
    DRY_RUN: bool = False
    
    # Agent settings
    AGENT_MEMORY_SIZE: int = 10
    FEEDBACK_THRESHOLD: float = 0.7
    
    class Config:
        """
        Additional configuration for settings.
        """
        env_file = ".env"
        case_sensitive = True

# Create a global instance of settings
settings = Settings()
