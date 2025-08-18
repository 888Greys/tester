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


@app.get("/deployment-info")
async def deployment_info():
    """
    Deployment information endpoint.
    Returns current deployment timestamp and version info.
    """
    return {
        "deployment_time": datetime.now().isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "status": "deployed",
        "message": "Gukas AI Agent is running successfully!"
    }


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
            dependencies={
                **dependencies,
                "deployment_timestamp": datetime.now().isoformat(),
                "uptime_check": "Service is running"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            app_name=settings.app_name,
            version=settings.app_version,
            dependencies={
                "error": str(e),
                "deployment_timestamp": datetime.now().isoformat()
            }
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


@app.post("/api/user/context/sync")
async def sync_user_context(request: Dict[str, Any]):
    """
    Sync user context from Django backend.
    Called when user logs in to synchronize their profile data.
    """
    try:
        user_id = request.get("user_id")
        context_data = request.get("context_data", {})
        sync_type = request.get("sync_type", "login")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Syncing user context for user {user_id} (type: {sync_type})")
        
        # Extract user info from context data
        user_info = context_data.get("user_info", {})
        farmer_profile = context_data.get("farmer_profile", {})
        farms_data = context_data.get("farms", {})
        
        # Create or update user profile in memory system
        profile_data = {
            "name": user_info.get("first_name", "") + " " + user_info.get("last_name", ""),
            "location": farmer_profile.get("location", ""),
            "farm_size_acres": farmer_profile.get("farm_size_acres"),
            "coffee_varieties": farmer_profile.get("coffee_varieties", ""),
            "farming_experience_years": farmer_profile.get("years_of_experience"),
        }
        
        # Remove None values
        profile_data = {k: v for k, v in profile_data.items() if v is not None}
        
        # Create or update user profile
        await memory_service.get_or_create_user_profile(
            user_id=str(user_id),
            **profile_data
        )
        
        # Store context summary as a memory embedding for future reference
        context_summary = context_data.get("summary", "")
        if context_summary:
            await memory_service.store_conversation_message(
                session_id=f"context_sync_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=str(user_id),
                message_type="system",
                content=f"User context: {context_summary}",
                metadata={
                    "sync_type": sync_type,
                    "context_version": request.get("context_version", "v1"),
                    "farms_count": farms_data.get("total_farms", 0),
                    "total_acres": sum(farm.get("size_acres", 0) for farm in farms_data.get("farms", []))
                }
            )
        
        return {
            "success": True,
            "user_id": str(user_id),
            "operation": "sync",
            "message": "User context synchronized successfully",
            "context_version": f"v1_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context sync failed: {str(e)}")


@app.put("/api/user/context/update")
async def update_user_context(request: Dict[str, Any]):
    """
    Update user context when profile data changes.
    Called when user updates their profile information.
    """
    try:
        user_id = request.get("user_id")
        updated_fields = request.get("updated_fields", [])
        context_data = request.get("context_data", {})
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Updating user context for user {user_id}, fields: {updated_fields}")
        
        # Extract updated user info
        user_info = context_data.get("user_info", {})
        farmer_profile = context_data.get("farmer_profile", {})
        
        # Prepare update data
        update_data = {}
        if "name" in updated_fields or "first_name" in updated_fields or "last_name" in updated_fields:
            update_data["name"] = user_info.get("first_name", "") + " " + user_info.get("last_name", "")
        if "location" in updated_fields:
            update_data["location"] = farmer_profile.get("location", "")
        if "farm_size_acres" in updated_fields:
            update_data["farm_size_acres"] = farmer_profile.get("farm_size_acres")
        if "coffee_varieties" in updated_fields:
            update_data["coffee_varieties"] = farmer_profile.get("coffee_varieties", "")
        if "years_of_experience" in updated_fields:
            update_data["farming_experience_years"] = farmer_profile.get("years_of_experience")
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update user profile
        if update_data:
            await memory_service.update_user_profile(str(user_id), **update_data)
        
        return {
            "success": True,
            "user_id": str(user_id),
            "operation": "update",
            "message": "User context updated successfully",
            "updated_fields": updated_fields,
            "context_version": f"v1_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context update failed: {str(e)}")


@app.delete("/api/user/context/clear")
async def clear_user_context(request: Dict[str, Any]):
    """
    Clear user context during logout or account deletion.
    """
    try:
        user_id = request.get("user_id")
        clear_type = request.get("clear_type", "logout")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Clearing user context for user {user_id} (type: {clear_type})")
        
        # For logout, we don't actually delete the user data, just log the event
        # For account deletion, we would need to implement actual data removal
        
        if clear_type == "account_deletion":
            # TODO: Implement actual user data deletion
            # This would involve removing user profile, conversations, etc.
            logger.warning(f"Account deletion requested for user {user_id} - not implemented yet")
        
        # Log the clear event
        await memory_service.store_conversation_message(
            session_id=f"context_clear_{user_id}_{datetime.utcnow().timestamp()}",
            user_id=str(user_id),
            message_type="system",
            content=f"User context cleared (type: {clear_type})",
            metadata={
                "clear_type": clear_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "user_id": str(user_id),
            "operation": "clear",
            "message": "User context cleared successfully",
            "clear_type": clear_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Context clear error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context clear failed: {str(e)}")


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
            "context_sync": True,  # Phase 2 ✅ - NEW!
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