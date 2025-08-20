"""
Memory Intelligence Service
Advanced memory management with automatic summarization, consolidation, and smart retrieval.
"""

import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

from app.database import db_manager
from app.services.embedding import vector_memory_service, embedding_service
from app.llm_client import cerebras_client
from app.models.memory import ConversationSession, ConversationMessage
from sqlalchemy import text, and_
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


@dataclass
class MemoryInsight:
    """Represents an important insight extracted from memory."""
    topic: str
    summary: str
    importance_score: float
    related_conversations: List[str]
    first_mentioned: datetime
    last_mentioned: datetime
    frequency: int


@dataclass
class ConversationSummary:
    """Represents a summarized conversation."""
    session_id: str
    summary: str
    key_topics: List[str]
    action_items: List[str]
    farming_insights: List[str]
    emotional_tone: str
    message_count: int
    duration_minutes: int


class MemoryIntelligenceService:
    """Advanced memory intelligence with summarization and smart retrieval."""
    
    def __init__(self):
        self.llm_client = cerebras_client
        self.vector_service = vector_memory_service
        self.embedding_service = embedding_service
    
    async def get_intelligent_memory_context(
        self, 
        query: str, 
        user_id: str,
        max_memories: int = 5,
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Get intelligent memory context with automatic relevance scoring and insights.
        
        Args:
            query: Current user query
            user_id: User ID
            max_memories: Maximum number of memories to return
            include_insights: Whether to include extracted insights
            
        Returns:
            Enhanced memory context with insights and summaries
        """
        try:
            # 1. Search for relevant conversations
            relevant_memories = await self.vector_service.search_similar_conversations(
                query_text=query,
                user_id=user_id,
                limit=max_memories * 2,  # Get more to filter intelligently
                similarity_threshold=0.6
            )
            
            # 2. Enhance memories with intelligent analysis
            enhanced_memories = await self._enhance_memory_relevance(
                memories=relevant_memories,
                current_query=query,
                user_id=user_id
            )
            
            # 3. Get conversation insights if requested
            insights = []
            if include_insights:
                insights = await self.get_memory_insights(user_id, limit=3)
            
            # 4. Build intelligent context
            context = {
                "relevant_memories": enhanced_memories[:max_memories],
                "memory_insights": insights,
                "context_summary": await self._build_context_summary(enhanced_memories, insights),
                "total_memories_found": len(relevant_memories),
                "confidence_score": self._calculate_context_confidence(enhanced_memories)
            }
            
            logger.info(f"Built intelligent memory context for user {user_id}: {len(enhanced_memories)} memories, {len(insights)} insights")
            return context
            
        except Exception as e:
            logger.error(f"Error building intelligent memory context: {e}")
            return {
                "relevant_memories": [],
                "memory_insights": [],
                "context_summary": "",
                "total_memories_found": 0,
                "confidence_score": 0.0
            }
    
    async def _enhance_memory_relevance(
        self,
        memories: List[Dict[str, Any]],
        current_query: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Enhance memory relevance with additional intelligence."""
        enhanced_memories = []
        
        for memory in memories:
            try:
                # Calculate enhanced relevance score
                relevance_factors = await self._calculate_enhanced_relevance(
                    memory, current_query, user_id
                )
                
                # Add enhanced metadata
                enhanced_memory = {
                    **memory,
                    "enhanced_relevance": relevance_factors["total_score"],
                    "relevance_factors": relevance_factors,
                    "memory_type": self._classify_memory_type(memory),
                    "key_entities": await self._extract_key_entities(memory["content"]),
                    "farming_context": self._extract_farming_context(memory["content"])
                }
                
                enhanced_memories.append(enhanced_memory)
                
            except Exception as e:
                logger.warning(f"Failed to enhance memory relevance: {e}")
                enhanced_memories.append(memory)
        
        # Sort by enhanced relevance
        enhanced_memories.sort(key=lambda x: x.get("enhanced_relevance", 0), reverse=True)
        return enhanced_memories
    
    async def _calculate_enhanced_relevance(
        self,
        memory: Dict[str, Any],
        current_query: str,
        user_id: str
    ) -> Dict[str, float]:
        """Calculate enhanced relevance score with multiple factors."""
        factors = {
            "semantic_similarity": memory.get("similarity_score", 0.0),
            "recency_score": 0.0,
            "frequency_score": 0.0,
            "topic_alignment": 0.0,
            "context_continuity": 0.0
        }
        
        try:
            # Calculate recency score (more recent = higher score)
            if "timestamp" in memory:
                timestamp = datetime.fromisoformat(memory["timestamp"].replace("Z", "+00:00"))
                days_ago = (datetime.utcnow().replace(tzinfo=timestamp.tzinfo) - timestamp).days
                factors["recency_score"] = max(0, 1.0 - (days_ago / 30))  # Decay over 30 days
            
            # Calculate topic alignment
            factors["topic_alignment"] = await self._calculate_topic_alignment(
                memory["content"], current_query
            )
            
            # Calculate context continuity (how well it fits the conversation flow)
            factors["context_continuity"] = await self._calculate_context_continuity(
                memory, current_query, user_id
            )
            
            # Calculate total weighted score
            weights = {
                "semantic_similarity": 0.4,
                "recency_score": 0.15,
                "frequency_score": 0.1,
                "topic_alignment": 0.2,
                "context_continuity": 0.15
            }
            
            total_score = sum(factors[key] * weights[key] for key in factors)
            factors["total_score"] = min(1.0, total_score)
            
        except Exception as e:
            logger.warning(f"Error calculating enhanced relevance: {e}")
            factors["total_score"] = factors["semantic_similarity"]
        
        return factors
    
    async def _calculate_topic_alignment(self, memory_content: str, current_query: str) -> float:
        """Calculate how well memory topic aligns with current query."""
        try:
            # Extract topics from both texts
            memory_topics = self._extract_farming_topics(memory_content)
            query_topics = self._extract_farming_topics(current_query)
            
            if not memory_topics or not query_topics:
                return 0.3  # Default alignment
            
            # Calculate topic overlap
            common_topics = set(memory_topics) & set(query_topics)
            alignment_score = len(common_topics) / max(len(query_topics), 1)
            
            return min(1.0, alignment_score)
            
        except Exception as e:
            logger.warning(f"Error calculating topic alignment: {e}")
            return 0.3
    
    def _extract_farming_topics(self, text: str) -> List[str]:
        """Extract farming-related topics from text."""
        farming_keywords = {
            "coffee": ["coffee", "arabica", "robusta", "sl28", "sl34", "ruiru", "batian"],
            "pests": ["cbd", "clr", "thrips", "mites", "aphids", "pests", "disease"],
            "weather": ["rain", "drought", "weather", "season", "climate"],
            "harvest": ["harvest", "picking", "processing", "drying", "milling"],
            "planting": ["planting", "seedlings", "nursery", "spacing"],
            "soil": ["soil", "fertilizer", "nutrition", "ph", "organic"],
            "market": ["price", "market", "selling", "buyer", "cooperative"]
        }
        
        text_lower = text.lower()
        found_topics = []
        
        for topic, keywords in farming_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_topics.append(topic)
        
        return found_topics
    
    async def _calculate_context_continuity(
        self,
        memory: Dict[str, Any],
        current_query: str,
        user_id: str
    ) -> float:
        """Calculate how well memory continues the conversation context."""
        try:
            # Check if memory is from a related conversation thread
            session_id = memory.get("session_id")
            if not session_id:
                return 0.3
            
            # Get recent messages from the same session
            async with db_manager.get_postgres_session() as session:
                recent_messages = await session.execute(
                    text("""
                        SELECT content, created_at 
                        FROM conversation_messages 
                        WHERE session_id = :session_id 
                        AND user_id = :user_id 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """),
                    {"session_id": session_id, "user_id": user_id}
                )
                
                messages = recent_messages.fetchall()
                
                if len(messages) > 1:
                    # Higher continuity score for conversations with multiple messages
                    return 0.8
                elif len(messages) == 1:
                    return 0.6
                else:
                    return 0.3
                    
        except Exception as e:
            logger.warning(f"Error calculating context continuity: {e}")
            return 0.3
    
    def _classify_memory_type(self, memory: Dict[str, Any]) -> str:
        """Classify the type of memory based on content."""
        content = memory.get("content", "").lower()
        
        if any(word in content for word in ["question", "?", "how", "what", "when", "where", "why"]):
            return "question"
        elif any(word in content for word in ["problem", "issue", "trouble", "help"]):
            return "problem_solving"
        elif any(word in content for word in ["thanks", "thank", "helpful", "great"]):
            return "positive_feedback"
        elif any(word in content for word in ["price", "sell", "buy", "market"]):
            return "market_inquiry"
        elif any(word in content for word in ["plant", "grow", "harvest", "fertilize"]):
            return "farming_activity"
        else:
            return "general_conversation"
    
    async def _extract_key_entities(self, content: str) -> List[str]:
        """Extract key entities from memory content."""
        # Simple entity extraction - can be enhanced with NLP models
        entities = []
        
        # Coffee varieties
        varieties = ["sl28", "sl34", "ruiru 11", "batian", "k7"]
        for variety in varieties:
            if variety in content.lower():
                entities.append(f"variety:{variety}")
        
        # Locations (Kenyan counties)
        counties = ["nyeri", "kiambu", "muranga", "kirinyaga", "embu", "meru"]
        for county in counties:
            if county in content.lower():
                entities.append(f"location:{county}")
        
        # Time references
        time_words = ["today", "yesterday", "week", "month", "season", "harvest time"]
        for time_word in time_words:
            if time_word in content.lower():
                entities.append(f"time:{time_word}")
        
        return entities
    
    def _extract_farming_context(self, content: str) -> Dict[str, Any]:
        """Extract farming-specific context from memory."""
        context = {
            "crop_mentioned": [],
            "activity_type": None,
            "season_reference": None,
            "problem_mentioned": False
        }
        
        content_lower = content.lower()
        
        # Crops
        crops = ["coffee", "maize", "beans", "tomatoes"]
        context["crop_mentioned"] = [crop for crop in crops if crop in content_lower]
        
        # Activities
        activities = ["planting", "harvesting", "pruning", "fertilizing", "spraying"]
        for activity in activities:
            if activity in content_lower:
                context["activity_type"] = activity
                break
        
        # Problems
        problems = ["disease", "pest", "drought", "rain", "problem"]
        context["problem_mentioned"] = any(problem in content_lower for problem in problems)
        
        return context
    
    async def _build_context_summary(
        self,
        memories: List[Dict[str, Any]],
        insights: List[MemoryInsight]
    ) -> str:
        """Build an intelligent context summary."""
        if not memories and not insights:
            return ""
        
        summary_parts = []
        
        if memories:
            # Summarize recent relevant conversations
            recent_topics = []
            for memory in memories[:3]:
                farming_context = memory.get("farming_context", {})
                if farming_context.get("crop_mentioned"):
                    recent_topics.extend(farming_context["crop_mentioned"])
            
            if recent_topics:
                unique_topics = list(set(recent_topics))
                summary_parts.append(f"Recent conversations about: {', '.join(unique_topics)}")
        
        if insights:
            # Summarize key insights
            insight_topics = [insight.topic for insight in insights[:2]]
            if insight_topics:
                summary_parts.append(f"Key farming insights: {', '.join(insight_topics)}")
        
        return "; ".join(summary_parts)
    
    def _calculate_context_confidence(self, memories: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in the memory context."""
        if not memories:
            return 0.0
        
        # Calculate average enhanced relevance
        relevance_scores = [
            memory.get("enhanced_relevance", memory.get("similarity_score", 0))
            for memory in memories
        ]
        
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # Boost confidence if we have multiple high-quality memories
        quality_boost = min(0.2, len([s for s in relevance_scores if s > 0.7]) * 0.1)
        
        return min(1.0, avg_relevance + quality_boost)
    
    async def get_memory_insights(
        self,
        user_id: str,
        limit: int = 5,
        min_frequency: int = 2
    ) -> List[MemoryInsight]:
        """Extract important insights from user's conversation history."""
        try:
            # Get all user conversations from the last 30 days
            async with db_manager.get_postgres_session() as session:
                messages = await session.execute(
                    text("""
                        SELECT content, created_at, session_id
                        FROM conversation_messages 
                        WHERE user_id = :user_id 
                        AND created_at > :cutoff_date
                        AND message_type = 'user'
                        ORDER BY created_at DESC
                    """),
                    {
                        "user_id": user_id,
                        "cutoff_date": datetime.utcnow() - timedelta(days=30)
                    }
                )
                
                conversation_data = messages.fetchall()
                
                if not conversation_data:
                    return []
                
                # Analyze conversations for patterns and insights
                insights = await self._analyze_conversation_patterns(conversation_data)
                
                # Filter and rank insights
                filtered_insights = [
                    insight for insight in insights 
                    if insight.frequency >= min_frequency and insight.importance_score > 0.5
                ]
                
                # Sort by importance and limit results
                filtered_insights.sort(key=lambda x: x.importance_score, reverse=True)
                return filtered_insights[:limit]
                
        except Exception as e:
            logger.error(f"Error extracting memory insights: {e}")
            return []
    
    async def _analyze_conversation_patterns(
        self,
        conversation_data: List[Tuple]
    ) -> List[MemoryInsight]:
        """Analyze conversation patterns to extract insights."""
        # Group conversations by topic
        topic_conversations = defaultdict(list)
        
        for content, created_at, session_id in conversation_data:
            topics = self._extract_farming_topics(content)
            for topic in topics:
                topic_conversations[topic].append({
                    "content": content,
                    "created_at": created_at,
                    "session_id": session_id
                })
        
        insights = []
        
        for topic, conversations in topic_conversations.items():
            if len(conversations) < 2:  # Skip topics mentioned only once
                continue
            
            # Calculate insight metrics
            frequency = len(conversations)
            first_mentioned = min(conv["created_at"] for conv in conversations)
            last_mentioned = max(conv["created_at"] for conv in conversations)
            
            # Generate summary using LLM
            summary = await self._generate_topic_summary(topic, conversations)
            
            # Calculate importance score
            importance_score = self._calculate_insight_importance(
                frequency, first_mentioned, last_mentioned, conversations
            )
            
            insight = MemoryInsight(
                topic=topic,
                summary=summary,
                importance_score=importance_score,
                related_conversations=[conv["session_id"] for conv in conversations],
                first_mentioned=first_mentioned,
                last_mentioned=last_mentioned,
                frequency=frequency
            )
            
            insights.append(insight)
        
        return insights
    
    async def _generate_topic_summary(
        self,
        topic: str,
        conversations: List[Dict[str, Any]]
    ) -> str:
        """Generate a summary of conversations about a specific topic."""
        try:
            # Combine recent conversations about the topic
            recent_conversations = sorted(
                conversations, 
                key=lambda x: x["created_at"], 
                reverse=True
            )[:5]
            
            conversation_text = "\n".join([
                f"- {conv['content']}" for conv in recent_conversations
            ])
            
            # Use LLM to generate summary
            prompt = f"""
            Analyze these farmer conversations about {topic} and provide a concise insight summary:
            
            Conversations:
            {conversation_text}
            
            Provide a 1-2 sentence summary of the key pattern or insight about this farmer's {topic} activities/concerns.
            Focus on actionable insights or recurring themes.
            """
            
            messages = [
                {"role": "system", "content": "You are an agricultural expert analyzing farmer conversation patterns."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_client.generate_response(messages)
            return response.get("content", f"Recurring topic: {topic}")
            
        except Exception as e:
            logger.warning(f"Error generating topic summary for {topic}: {e}")
            return f"Frequently discussed: {topic} ({len(conversations)} times)"
    
    def _calculate_insight_importance(
        self,
        frequency: int,
        first_mentioned: datetime,
        last_mentioned: datetime,
        conversations: List[Dict[str, Any]]
    ) -> float:
        """Calculate the importance score of an insight."""
        # Base score from frequency
        frequency_score = min(1.0, frequency / 10)  # Normalize to max 1.0
        
        # Recency score (more recent = more important)
        days_since_last = (datetime.utcnow().replace(tzinfo=last_mentioned.tzinfo) - last_mentioned).days
        recency_score = max(0, 1.0 - (days_since_last / 30))
        
        # Consistency score (spread over time = more important)
        time_span_days = (last_mentioned - first_mentioned).days
        consistency_score = min(1.0, time_span_days / 14)  # 2 weeks for full score
        
        # Combine scores with weights
        importance = (
            frequency_score * 0.4 +
            recency_score * 0.35 +
            consistency_score * 0.25
        )
        
        return min(1.0, importance)
    
    async def consolidate_session_memory(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[ConversationSummary]:
        """Consolidate a conversation session into a summary."""
        try:
            async with db_manager.get_postgres_session() as session:
                # Get all messages from the session
                messages = await session.execute(
                    text("""
                        SELECT content, message_type, created_at, tokens_used
                        FROM conversation_messages 
                        WHERE session_id = :session_id 
                        AND user_id = :user_id
                        ORDER BY created_at ASC
                    """),
                    {"session_id": session_id, "user_id": user_id}
                )
                
                message_data = messages.fetchall()
                
                if len(message_data) < 2:  # Need at least 2 messages for a conversation
                    return None
                
                # Build conversation summary
                summary = await self._generate_conversation_summary(message_data)
                
                # Calculate session metrics
                start_time = message_data[0][2]  # created_at of first message
                end_time = message_data[-1][2]   # created_at of last message
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
                
                conversation_summary = ConversationSummary(
                    session_id=session_id,
                    summary=summary["summary"],
                    key_topics=summary["key_topics"],
                    action_items=summary["action_items"],
                    farming_insights=summary["farming_insights"],
                    emotional_tone=summary["emotional_tone"],
                    message_count=len(message_data),
                    duration_minutes=duration_minutes
                )
                
                logger.info(f"Generated conversation summary for session {session_id}")
                return conversation_summary
                
        except Exception as e:
            logger.error(f"Error consolidating session memory: {e}")
            return None
    
    async def _generate_conversation_summary(
        self,
        message_data: List[Tuple]
    ) -> Dict[str, Any]:
        """Generate a comprehensive conversation summary using LLM."""
        try:
            # Build conversation text
            conversation_text = []
            for content, message_type, created_at, tokens_used in message_data:
                speaker = "Farmer" if message_type == "user" else "Guka"
                conversation_text.append(f"{speaker}: {content}")
            
            conversation = "\n".join(conversation_text)
            
            # Generate summary using LLM
            prompt = f"""
            Analyze this conversation between a Kenyan coffee farmer and Guka (AI farming assistant):

            {conversation}

            Provide a structured analysis with:
            1. Summary: 2-3 sentence overview of the conversation
            2. Key Topics: List of main farming topics discussed
            3. Action Items: Any specific actions or recommendations mentioned
            4. Farming Insights: Agricultural insights or learning points
            5. Emotional Tone: Overall tone (professional, concerned, positive, etc.)

            Format as JSON with keys: summary, key_topics, action_items, farming_insights, emotional_tone
            """
            
            messages = [
                {"role": "system", "content": "You are an expert at analyzing agricultural conversations. Provide structured JSON responses."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_client.generate_response(messages)
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response.get("content", "{}"))
            except json.JSONDecodeError:
                # Fallback to simple analysis
                return self._fallback_conversation_analysis(message_data)
                
        except Exception as e:
            logger.warning(f"Error generating conversation summary: {e}")
            return self._fallback_conversation_analysis(message_data)
    
    def _fallback_conversation_analysis(self, message_data: List[Tuple]) -> Dict[str, Any]:
        """Fallback conversation analysis when LLM fails."""
        user_messages = [content for content, msg_type, _, _ in message_data if msg_type == "user"]
        all_content = " ".join([content for content, _, _, _ in message_data])
        
        # Extract topics
        topics = self._extract_farming_topics(all_content)
        
        return {
            "summary": f"Conversation about {', '.join(topics[:3]) if topics else 'general farming'} with {len(user_messages)} farmer questions.",
            "key_topics": topics[:5],
            "action_items": [],
            "farming_insights": [],
            "emotional_tone": "professional"
        }


# Global service instance
memory_intelligence_service = MemoryIntelligenceService()
