"""
Pydantic models for request/response validation.
Defines the API contract for the agent service.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How is my coffee farm doing?",
                "user_id": "farmer_123",
                "session_id": "session_456",
                "context": {"farm_id": 1}
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    model_used: str = Field(..., description="LLM model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your coffee farm is looking great! Based on the latest data...",
                "session_id": "session_456",
                "timestamp": "2024-08-09T09:30:00Z",
                "model_used": "llama3.1-70b",
                "tokens_used": 150
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "app_name": "Gukas AI Agent",
                "version": "1.0.0",
                "timestamp": "2024-08-09T09:30:00Z",
                "dependencies": {
                    "cerebras_api": "connected",
                    "django_backend": "connected"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request format",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2024-08-09T09:30:00Z",
                "request_id": "req_123456"
            }
        }