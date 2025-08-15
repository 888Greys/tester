"""
SQLAlchemy models for memory system.
Defines database models for user profiles, conversations, and memory storage.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, ARRAY
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional
import uuid

from app.database import Base


class UserProfile(Base):
    """User profile model for storing farmer information."""
    
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    location = Column(String(255))
    farm_size_acres = Column(Numeric(10, 2))
    coffee_varieties = Column(ARRAY(Text))
    farming_experience_years = Column(Integer)
    preferred_language = Column(String(10), default='en')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversation_sessions = relationship("ConversationSession", back_populates="user_profile", cascade="all, delete-orphan")
    conversation_messages = relationship("ConversationMessage", back_populates="user_profile", cascade="all, delete-orphan")
    farm_contexts = relationship("FarmContext", back_populates="user_profile", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', name='{self.name}')>"


class ConversationSession(Base):
    """Conversation session model for grouping related messages."""
    
    __tablename__ = "conversation_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    message_count = Column(Integer, default=0)
    context = Column(JSONB, default={})
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="conversation_sessions")
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConversationSession(session_id='{self.session_id}', user_id='{self.user_id}')>"


class ConversationMessage(Base):
    """Individual message model for storing conversation history."""
    
    __tablename__ = "conversation_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("conversation_sessions.session_id"), nullable=False, index=True)
    user_id = Column(String(255), ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    message_metadata = Column(JSONB, default={})
    
    # Relationships
    session = relationship("ConversationSession", back_populates="messages")
    user_profile = relationship("UserProfile", back_populates="conversation_messages")
    memory_embeddings = relationship("MemoryEmbedding", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ConversationMessage(id='{self.id}', type='{self.message_type}')>"


class MemoryEmbedding(Base):
    """Memory embedding model for vector search references."""
    
    __tablename__ = "memory_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.id"), nullable=False, index=True)
    qdrant_point_id = Column(UUID(as_uuid=True), nullable=False)
    embedding_model = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("ConversationMessage", back_populates="memory_embeddings")
    
    def __repr__(self):
        return f"<MemoryEmbedding(message_id='{self.message_id}', model='{self.embedding_model}')>"


class FarmContext(Base):
    """Farm context model for linking to Django backend data."""
    
    __tablename__ = "farm_context"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    django_farm_id = Column(Integer)
    farm_name = Column(String(255))
    last_sync = Column(DateTime(timezone=True), server_default=func.now())
    context_data = Column(JSONB, default={})
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="farm_contexts")
    
    def __repr__(self):
        return f"<FarmContext(user_id='{self.user_id}', farm_name='{self.farm_name}')>"
