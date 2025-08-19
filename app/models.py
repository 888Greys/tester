"""
Pydantic models for request/response validation.
Defines the API contract for the agent service.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "How is my coffee farm doing?",
                "user_id": "farmer_123",
                "session_id": "session_456",
                "context": {"farm_id": 1}
            }
        }
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    model_used: str = Field(..., description="LLM model used")
    tokens_used: Optional[int] = Field(None, description="Tokens consumed")
    
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "response": "Your coffee farm is looking great! Based on the latest data...",
                "session_id": "session_456",
                "timestamp": "2024-08-09T09:30:00Z",
                "model_used": "llama3.1-70b",
                "tokens_used": 150
            }
        }
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "app_name": "Guka's AI Agent",
                "version": "1.0.0",
                "timestamp": "2024-08-09T09:30:00Z",
                "dependencies": {
                    "cerebras_api": "connected",
                    "django_backend": "connected"
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Invalid request format",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2024-08-09T09:30:00Z",
                "request_id": "req_123456"
            }
        }
    )


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    chunk_count: int = Field(..., description="Number of chunks created")
    upload_date: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    message: str = Field(default="Document uploaded successfully", description="Success message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "doc_12345",
                "filename": "coffee_farming_guide.pdf",
                "file_size": 1024000,
                "chunk_count": 15,
                "upload_date": "2024-08-09T09:30:00Z",
                "message": "Document uploaded successfully"
            }
        }
    )


class DocumentSearchRequest(BaseModel):
    """Request model for document search endpoint."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    user_id: Optional[str] = Field(None, description="User ID to filter documents")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity score")
    tags: Optional[List[str]] = Field(None, description="Filter by document tags")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "coffee plant diseases",
                "user_id": "farmer_123",
                "limit": 5,
                "similarity_threshold": 0.3,
                "tags": ["coffee", "farming"]
            }
        }
    )


class DocumentSearchResponse(BaseModel):
    """Response model for document search endpoint."""
    
    query: str = Field(..., description="Original search query")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    total_found: int = Field(..., description="Number of results found")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "coffee plant diseases",
                "results": [
                    {
                        "document_id": "doc_123",
                        "filename": "coffee_diseases.pdf",
                        "content": "Coffee berry disease is a major concern...",
                        "similarity_score": 0.85,
                        "chunk_index": 2
                    }
                ],
                "total_found": 1
            }
        }
    )


class DocumentListResponse(BaseModel):
    """Response model for document listing endpoint."""
    
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="List of documents")
    total: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset for pagination")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "document_id": "doc_123",
                        "filename": "coffee_farming_guide.pdf",
                        "file_size": 1024000,
                        "file_type": "application/pdf",
                        "description": "Complete guide to coffee farming",
                        "tags": ["coffee", "farming", "guide"],
                        "chunk_count": 15,
                        "upload_date": "2024-08-09T09:30:00Z",
                        "user_id": "farmer_123"
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0
            }
        }
    )
