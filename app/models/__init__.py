"""
Models package for Gukas AI Agent.
Contains Pydantic models and SQLAlchemy models.
"""

import sys
import os
import importlib.util

# Import Pydantic models from the original models.py
from app.models.api_models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse

# Import document models from the root models.py file
# Using absolute import to avoid circular import
models_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.py')
spec = importlib.util.spec_from_file_location("document_models", models_file_path)
document_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(document_models)

DocumentUploadResponse = document_models.DocumentUploadResponse
DocumentSearchRequest = document_models.DocumentSearchRequest
DocumentSearchResponse = document_models.DocumentSearchResponse
DocumentListResponse = document_models.DocumentListResponse

# Import SQLAlchemy models
from app.models.memory import UserProfile, ConversationSession, ConversationMessage, MemoryEmbedding, FarmContext

__all__ = [
    # API Models
    "ChatRequest",
    "ChatResponse", 
    "HealthResponse",
    "ErrorResponse",
    
    # Document Models
    "DocumentUploadResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    "DocumentListResponse",
    
    # Memory Models
    "UserProfile",
    "ConversationSession",
    "ConversationMessage", 
    "MemoryEmbedding",
    "FarmContext"
]
