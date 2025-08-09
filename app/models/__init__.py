"""
Models package for Gukas AI Agent.
Contains Pydantic models and SQLAlchemy models.
"""

# Import Pydantic models from the original models.py
from app.models.api_models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse

# Import SQLAlchemy models
from app.models.memory import UserProfile, ConversationSession, ConversationMessage, MemoryEmbedding, FarmContext

__all__ = [
    # API Models
    "ChatRequest",
    "ChatResponse", 
    "HealthResponse",
    "ErrorResponse",
    
    # Memory Models
    "UserProfile",
    "ConversationSession",
    "ConversationMessage", 
    "MemoryEmbedding",
    "FarmContext"
]