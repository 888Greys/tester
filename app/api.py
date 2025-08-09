"""
FastAPI application and route definitions.
Main API endpoints for the Gukas AI Agent with memory system.
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
from app.database import db_manager
from app.services.embedding import vector_memory_service
from app.services.memory import memory_service

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
    description="AI-powered coffee farming assistant for Kenyan farmers with memory",
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


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        logger.info("Initializing database connections...")
        await db_manager.initialize()
        
        logger.info("Initializing vector memory service...")
        await vector_memory_service.initialize()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        logger.info("Closing database connections...")
        await db_manager.close()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


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
        # Check agent service
        agent_dependencies = await agent_service.health_check()
        
        # Check database connections
        db_health = await db_manager.health_check()
        
        # Combine all dependencies
        dependencies = {
            **agent_dependencies,
            **db_health
        }
        
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
    Main chat endpoint for farmer interactions with memory.
    Processes messages and returns AI-generated responses with context.
    """
    try:
        logger.info(f"Received chat request from user: {request.user_id}")
        
        # Get or create user profile
        if request.user_id:
            await memory_service.get_or_create_user_profile(request.user_id)
        
        # Search for relevant memories
        relevant_memories = []
        if request.user_id and request.message:
            relevant_memories = await memory_service.search_relevant_memories(
                user_id=request.user_id,
                query_text=request.message,
                limit=3,
                similarity_threshold=0.7,
                exclude_session=request.session_id
            )
        
        # Add memory context to request
        enhanced_context = {
            **(request.context or {}),
            "relevant_memories": relevant_memories
        }
        
        # Create enhanced request
        enhanced_request = ChatRequest(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            context=enhanced_context
        )
        
        # Process the chat message with memory context
        response = await agent_service.process_chat_message(enhanced_request)
        
        # Store user message in memory
        if request.user_id:
            await memory_service.store_conversation_message(
                session_id=response.session_id,
                user_id=request.user_id,
                message_type="user",
                content=request.message,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            
            # Store agent response in memory
            await memory_service.store_conversation_message(
                session_id=response.session_id,
                user_id=request.user_id,
                message_type="assistant",
                content=response.response,
                tokens_used=response.tokens_used,
                model_used=response.model_used,
                metadata={"timestamp": response.timestamp.isoformat()}
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@app.get("/memory/user/{user_id}")
async def get_user_memory(user_id: str):
    """Get user memory statistics and recent activity."""
    try:
        stats = await memory_service.get_user_stats(user_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 10):
    """Get recent conversation sessions for a user."""
    try:
        sessions = await memory_service.get_user_conversation_sessions(
            user_id=user_id,
            limit=limit
        )
        
        session_data = []
        for session in sessions:
            session_data.append({
                "session_id": session.session_id,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": session.message_count,
                "context": session.context
            })
        
        return {"sessions": session_data}
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/conversation/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 50):
    """Get conversation history for a session."""
    try:
        messages = await memory_service.get_conversation_history(
            session_id=session_id,
            limit=limit
        )
        
        message_data = []
        for message in messages:
            message_data.append({
                "id": str(message.id),
                "message_type": message.message_type,
                "content": message.content,
                "tokens_used": message.tokens_used,
                "model_used": message.model_used,
                "created_at": message.created_at.isoformat(),
                "metadata": message.metadata
            })
        
        return {"messages": message_data}
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def search_memories(request: Dict[str, Any]):
    """Search for relevant memories using semantic search."""
    try:
        user_id = request.get("user_id")
        query = request.get("query")
        limit = request.get("limit", 5)
        
        if not user_id or not query:
            raise HTTPException(
                status_code=400, 
                detail="user_id and query are required"
            )
        
        memories = await memory_service.search_relevant_memories(
            user_id=user_id,
            query_text=query,
            limit=limit
        )
        
        return {"memories": memories}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs" if settings.debug else "disabled",
        "features": {
            "memory": True,
            "vector_search": True,
            "user_profiles": True
        }
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
            "memory": True,  # Phase 2 ✅
            "vector_search": True,  # Phase 2 ✅
            "user_profiles": True,  # Phase 2 ✅
            "documents": False,  # Phase 4
            "tools": False  # Phase 3
        },
        "databases": {
            "postgres": f"{settings.postgres_host}:{settings.postgres_port}",
            "qdrant": f"{settings.qdrant_host}:{settings.qdrant_port}",
            "redis": f"{settings.redis_host}:{settings.redis_port}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Cerebras model: {settings.cerebras_model}")
    logger.info(f"Memory system: enabled")
    
    uvicorn.run(
        "app.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )