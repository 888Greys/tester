"""
FastAPI application and route definitions.
Main API endpoints for the Gukas AI Agent.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse
from app.services import agent_service, context_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered coffee farming assistant for Kenyan farmers",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception [{request_id}]: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            request_id=request_id
        ).dict()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns service status and dependency health.
    """
    try:
        dependencies = await agent_service.health_check()
        
        # Determine overall status
        status = "healthy" if all(
            dep_status in ["connected", "not_configured"] 
            for dep_status in dependencies.values()
        ) else "degraded"
        
        return HealthResponse(
            status=status,
            app_name=settings.app_name,
            version=settings.app_version,
            dependencies=dependencies
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            app_name=settings.app_name,
            version=settings.app_version,
            dependencies={"error": str(e)}
        )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for farmer interactions.
    Processes messages and returns AI-generated responses.
    """
    try:
        logger.info(f"Received chat request from user: {request.user_id}")
        
        # Process the chat message
        response = await agent_service.process_chat_message(request)
        
        # Save conversation (placeholder for Phase 2)
        await context_service.save_conversation(
            session_id=response.session_id,
            user_message=request.message,
            agent_response=response.response,
            user_id=request.user_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.get("/info")
async def service_info():
    """Service information endpoint."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug_mode": settings.debug,
        "cerebras_model": settings.cerebras_model,
        "django_backend": settings.django_base_url,
        "features": {
            "chat": True,
            "memory": False,  # Phase 2
            "documents": False,  # Phase 4
            "tools": False  # Phase 3
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Cerebras model: {settings.cerebras_model}")
    
    uvicorn.run(
        "app.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )