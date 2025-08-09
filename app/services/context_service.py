"""
Context service for managing user context and session data.
Legacy service maintained for compatibility.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContextService:
    """Service for managing user context and session data."""
    
    def __init__(self):
        """Initialize context service."""
        logger.info("Context service initialized (legacy compatibility)")
    
    async def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user context from storage.
        
        Args:
            user_id: User identifier
            
        Returns:
            User context dictionary or None
        """
        logger.info(f"Getting context for user: {user_id} (legacy method)")
        # This is now handled by memory_service
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
        logger.info(f"Saving conversation for session: {session_id} (legacy method)")
        # This is now handled by memory_service in the API layer
        pass


# Global service instance
context_service = ContextService()