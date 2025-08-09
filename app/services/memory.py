"""
Memory management service for conversation storage and retrieval.
Handles user profiles, conversation sessions, and memory operations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.database import db_manager
from app.models.memory import UserProfile, ConversationSession, ConversationMessage, MemoryEmbedding, FarmContext
from app.services.embedding import vector_memory_service

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing conversation memory and user profiles."""
    
    async def get_or_create_user_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        **profile_data
    ) -> UserProfile:
        """Get existing user profile or create new one."""
        async with db_manager.get_postgres_session() as session:
            try:
                # Try to get existing profile
                result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                
                if profile:
                    # Update profile if new data provided
                    if name or profile_data:
                        if name:
                            profile.name = name
                        for key, value in profile_data.items():
                            if hasattr(profile, key) and value is not None:
                                setattr(profile, key, value)
                        await session.commit()
                        await session.refresh(profile)
                    
                    logger.info(f"Retrieved existing user profile for {user_id}")
                    return profile
                
                # Create new profile
                profile = UserProfile(
                    user_id=user_id,
                    name=name,
                    **profile_data
                )
                session.add(profile)
                await session.commit()
                await session.refresh(profile)
                
                logger.info(f"Created new user profile for {user_id}")
                return profile
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to get/create user profile: {e}")
                raise
    
    async def get_or_create_conversation_session(
        self,
        session_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Get existing conversation session or create new one."""
        async with db_manager.get_postgres_session() as session_db:
            try:
                # Try to get existing session
                result = await session_db.execute(
                    select(ConversationSession).where(
                        ConversationSession.session_id == session_id
                    )
                )
                conv_session = result.scalar_one_or_none()
                
                if conv_session:
                    # Update last activity
                    conv_session.last_activity = datetime.utcnow()
                    if context:
                        conv_session.context = {**conv_session.context, **context}
                    await session_db.commit()
                    await session_db.refresh(conv_session)
                    
                    logger.info(f"Retrieved existing conversation session {session_id}")
                    return conv_session
                
                # Ensure user profile exists
                await self.get_or_create_user_profile(user_id)
                
                # Create new session
                conv_session = ConversationSession(
                    session_id=session_id,
                    user_id=user_id,
                    context=context or {}
                )
                session_db.add(conv_session)
                await session_db.commit()
                await session_db.refresh(conv_session)
                
                logger.info(f"Created new conversation session {session_id}")
                return conv_session
                
            except Exception as e:
                await session_db.rollback()
                logger.error(f"Failed to get/create conversation session: {e}")
                raise
    
    async def store_conversation_message(
        self,
        session_id: str,
        user_id: str,
        message_type: str,
        content: str,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Store a conversation message with vector embedding."""
        async with db_manager.get_postgres_session() as session_db:
            try:
                # Ensure session exists
                await self.get_or_create_conversation_session(session_id, user_id)
                
                # Create message
                message = ConversationMessage(
                    session_id=session_id,
                    user_id=user_id,
                    message_type=message_type,
                    content=content,
                    tokens_used=tokens_used,
                    model_used=model_used,
                    metadata=metadata or {}
                )
                session_db.add(message)
                await session_db.commit()
                await session_db.refresh(message)
                
                # Store vector embedding
                try:
                    point_id = await vector_memory_service.store_conversation_memory(
                        message_id=str(message.id),
                        user_id=user_id,
                        session_id=session_id,
                        content=content,
                        message_type=message_type,
                        metadata={
                            "timestamp": message.created_at.isoformat(),
                            "tokens_used": tokens_used,
                            "model_used": model_used,
                            **(metadata or {})
                        }
                    )
                    
                    # Store embedding reference
                    embedding_ref = MemoryEmbedding(
                        message_id=message.id,
                        qdrant_point_id=point_id,
                        embedding_model="all-MiniLM-L6-v2"
                    )
                    session_db.add(embedding_ref)
                    await session_db.commit()
                    
                except Exception as e:
                    logger.warning(f"Failed to store vector embedding: {e}")
                    # Continue without vector embedding
                
                logger.info(f"Stored conversation message for session {session_id}")
                return message
                
            except Exception as e:
                await session_db.rollback()
                logger.error(f"Failed to store conversation message: {e}")
                raise
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        include_embeddings: bool = False
    ) -> List[ConversationMessage]:
        """Get conversation history for a session."""
        async with db_manager.get_postgres_session() as session:
            try:
                query = select(ConversationMessage).where(
                    ConversationMessage.session_id == session_id
                ).order_by(ConversationMessage.created_at)
                
                if include_embeddings:
                    query = query.options(selectinload(ConversationMessage.memory_embeddings))
                
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                messages = result.scalars().all()
                
                logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
                return list(messages)
                
            except Exception as e:
                logger.error(f"Failed to get conversation history: {e}")
                return []
    
    async def get_user_conversation_sessions(
        self,
        user_id: str,
        limit: int = 20,
        days_back: int = 30
    ) -> List[ConversationSession]:
        """Get recent conversation sessions for a user."""
        async with db_manager.get_postgres_session() as session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                
                query = select(ConversationSession).where(
                    and_(
                        ConversationSession.user_id == user_id,
                        ConversationSession.last_activity >= cutoff_date
                    )
                ).order_by(desc(ConversationSession.last_activity))
                
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                sessions = result.scalars().all()
                
                logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
                return list(sessions)
                
            except Exception as e:
                logger.error(f"Failed to get user conversation sessions: {e}")
                return []
    
    async def search_relevant_memories(
        self,
        user_id: str,
        query_text: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        exclude_session: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories using vector similarity."""
        try:
            # Search vector database
            similar_conversations = await vector_memory_service.search_similar_conversations(
                query_text=query_text,
                user_id=user_id,
                limit=limit * 2,  # Get more to filter
                similarity_threshold=similarity_threshold
            )
            
            # Filter out current session if specified
            if exclude_session:
                similar_conversations = [
                    conv for conv in similar_conversations 
                    if conv.get("session_id") != exclude_session
                ]
            
            # Limit results
            similar_conversations = similar_conversations[:limit]
            
            # Enrich with database information if needed
            enriched_memories = []
            async with db_manager.get_postgres_session() as session:
                for memory in similar_conversations:
                    message_id = memory.get("message_id")
                    if message_id:
                        try:
                            # Get full message details
                            result = await session.execute(
                                select(ConversationMessage).where(
                                    ConversationMessage.id == message_id
                                )
                            )
                            message = result.scalar_one_or_none()
                            
                            if message:
                                enriched_memories.append({
                                    **memory,
                                    "full_content": message.content,
                                    "created_at": message.created_at.isoformat(),
                                    "tokens_used": message.tokens_used,
                                    "model_used": message.model_used
                                })
                            else:
                                enriched_memories.append(memory)
                        except Exception as e:
                            logger.warning(f"Failed to enrich memory {message_id}: {e}")
                            enriched_memories.append(memory)
                    else:
                        enriched_memories.append(memory)
            
            logger.info(f"Found {len(enriched_memories)} relevant memories for user {user_id}")
            return enriched_memories
            
        except Exception as e:
            logger.error(f"Failed to search relevant memories: {e}")
            return []
    
    async def update_user_profile(
        self,
        user_id: str,
        **updates
    ) -> Optional[UserProfile]:
        """Update user profile information."""
        async with db_manager.get_postgres_session() as session:
            try:
                result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"User profile not found for {user_id}")
                    return None
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(profile, key) and value is not None:
                        setattr(profile, key, value)
                
                await session.commit()
                await session.refresh(profile)
                
                logger.info(f"Updated user profile for {user_id}")
                return profile
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user profile: {e}")
                return None
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics and activity summary."""
        async with db_manager.get_postgres_session() as session:
            try:
                # Get user profile
                profile_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = profile_result.scalar_one_or_none()
                
                if not profile:
                    return {}
                
                # Get session count
                session_count_result = await session.execute(
                    select(ConversationSession).where(
                        ConversationSession.user_id == user_id
                    )
                )
                session_count = len(session_count_result.scalars().all())
                
                # Get message count
                message_count_result = await session.execute(
                    select(ConversationMessage).where(
                        ConversationMessage.user_id == user_id
                    )
                )
                message_count = len(message_count_result.scalars().all())
                
                # Get recent activity
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                recent_activity_result = await session.execute(
                    select(ConversationSession).where(
                        and_(
                            ConversationSession.user_id == user_id,
                            ConversationSession.last_activity >= recent_cutoff
                        )
                    )
                )
                recent_sessions = len(recent_activity_result.scalars().all())
                
                stats = {
                    "user_id": user_id,
                    "name": profile.name,
                    "location": profile.location,
                    "farm_size_acres": float(profile.farm_size_acres) if profile.farm_size_acres else None,
                    "coffee_varieties": profile.coffee_varieties,
                    "farming_experience_years": profile.farming_experience_years,
                    "total_sessions": session_count,
                    "total_messages": message_count,
                    "recent_sessions_7d": recent_sessions,
                    "member_since": profile.created_at.isoformat(),
                    "last_updated": profile.updated_at.isoformat()
                }
                
                logger.info(f"Retrieved stats for user {user_id}")
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get user stats: {e}")
                return {}


# Global service instance
memory_service = MemoryService()