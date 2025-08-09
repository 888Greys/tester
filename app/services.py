"""
Business logic services for the AI agent.
Contains the core agent functionality and orchestration.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from app.llm_client import cerebras_client, AgentPrompts
from app.models import ChatRequest, ChatResponse
from app.config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Core agent service handling chat interactions."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.llm_client = cerebras_client
        
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and generate response.
        
        Args:
            request: Chat request containing message and context
            
        Returns:
            Chat response with agent's reply
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Generate session ID if not provided
            session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Processing chat message for session: {session_id}")
            
            # Build messages for LLM
            messages = AgentPrompts.build_messages(
                user_message=request.message,
                context=request.context
            )
            
            # Generate response from Cerebras
            llm_response = await self.llm_client.generate_response(messages)
            
            # Create response object
            response = ChatResponse(
                response=llm_response["content"],
                session_id=session_id,
                model_used=llm_response["model"],
                tokens_used=llm_response["tokens_used"]
            )
            
            logger.info(f"Chat response generated for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise Exception(f"Failed to process chat message: {str(e)}")
    
    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on agent dependencies.
        
        Returns:
            Dictionary with dependency status
        """
        dependencies = {}
        
        # Check Cerebras API
        try:
            cerebras_healthy = await self.llm_client.health_check()
            dependencies["cerebras_api"] = "connected" if cerebras_healthy else "disconnected"
        except Exception as e:
            logger.error(f"Cerebras health check error: {str(e)}")
            dependencies["cerebras_api"] = "error"
        
        # Check Django backend (placeholder for Phase 2)
        dependencies["django_backend"] = "not_configured"
        
        return dependencies


class ContextService:
    """Service for managing user context and session data."""
    
    def __init__(self):
        """Initialize context service."""
        # Placeholder for Phase 2 - will integrate with memory system
        pass
    
    async def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user context from storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            User context dictionary or None
        """
        # Placeholder implementation for Phase 1
        # Will be implemented in Phase 2 with database integration
        logger.info(f"Getting context for user: {user_id}")
        return None
    
    async def save_conversation(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Save conversation to storage.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            agent_response: Agent's response
            user_id: Optional user identifier
        """
        # Placeholder implementation for Phase 1
        # Will be implemented in Phase 2 with database integration
        logger.info(f"Saving conversation for session: {session_id}")
        pass


# Global service instances
agent_service = AgentService()
context_service = ContextService()