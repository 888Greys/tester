"""
Memory Intelligence API endpoints for advanced memory management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging

from app.services.memory_intelligence import memory_intelligence_service, MemoryInsight, ConversationSummary
from app.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory-intelligence", tags=["Memory Intelligence"])


@router.get("/insights/{user_id}")
async def get_memory_insights(
    user_id: str,
    limit: int = 5,
    min_frequency: int = 2
) -> List[Dict[str, Any]]:
    """
    Get intelligent insights from user's conversation history.
    
    Args:
        user_id: User ID
        limit: Maximum number of insights to return
        min_frequency: Minimum frequency for topic to be considered
        
    Returns:
        List of memory insights
    """
    try:
        insights = await memory_intelligence_service.get_memory_insights(
            user_id=user_id,
            limit=limit,
            min_frequency=min_frequency
        )
        
        # Convert insights to dict format
        insights_data = []
        for insight in insights:
            insights_data.append({
                "topic": insight.topic,
                "summary": insight.summary,
                "importance_score": insight.importance_score,
                "frequency": insight.frequency,
                "first_mentioned": insight.first_mentioned.isoformat(),
                "last_mentioned": insight.last_mentioned.isoformat(),
                "related_conversations": insight.related_conversations
            })
        
        return insights_data
        
    except Exception as e:
        logger.error(f"Error getting memory insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/context/{user_id}")
async def get_intelligent_context(
    user_id: str,
    query: str,
    max_memories: int = 5,
    include_insights: bool = True
) -> Dict[str, Any]:
    """
    Get intelligent memory context for a query.
    
    Args:
        user_id: User ID
        query: Current query to find relevant context for
        max_memories: Maximum number of memories to return
        include_insights: Whether to include extracted insights
        
    Returns:
        Enhanced memory context with insights
    """
    try:
        context = await memory_intelligence_service.get_intelligent_memory_context(
            query=query,
            user_id=user_id,
            max_memories=max_memories,
            include_insights=include_insights
        )
        
        # Convert insights to serializable format
        if "memory_insights" in context:
            context["memory_insights"] = [
                {
                    "topic": insight.topic,
                    "summary": insight.summary,
                    "importance_score": insight.importance_score,
                    "frequency": insight.frequency
                }
                for insight in context["memory_insights"]
            ]
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting intelligent context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.post("/consolidate/{session_id}")
async def consolidate_session(
    session_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Consolidate a conversation session into a summary.
    
    Args:
        session_id: Session ID to consolidate
        user_id: User ID
        
    Returns:
        Conversation summary
    """
    try:
        summary = await memory_intelligence_service.consolidate_session_memory(
            session_id=session_id,
            user_id=user_id
        )
        
        if not summary:
            raise HTTPException(
                status_code=404, 
                detail="Session not found or insufficient messages for summary"
            )
        
        return {
            "session_id": summary.session_id,
            "summary": summary.summary,
            "key_topics": summary.key_topics,
            "action_items": summary.action_items,
            "farming_insights": summary.farming_insights,
            "emotional_tone": summary.emotional_tone,
            "message_count": summary.message_count,
            "duration_minutes": summary.duration_minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consolidating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to consolidate session: {str(e)}")


@router.get("/analysis/{user_id}")
async def get_memory_analysis(
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get comprehensive memory analysis for a user.
    
    Args:
        user_id: User ID
        days: Number of days to analyze
        
    Returns:
        Memory analysis with patterns and insights
    """
    try:
        # Get insights and context
        insights = await memory_intelligence_service.get_memory_insights(
            user_id=user_id,
            limit=10
        )
        
        # Analyze patterns
        analysis = {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_insights": len(insights),
            "insights": [
                {
                    "topic": insight.topic,
                    "summary": insight.summary,
                    "importance_score": insight.importance_score,
                    "frequency": insight.frequency,
                    "first_mentioned": insight.first_mentioned.isoformat(),
                    "last_mentioned": insight.last_mentioned.isoformat()
                }
                for insight in insights
            ],
            "top_topics": [insight.topic for insight in insights[:5]],
            "engagement_patterns": _analyze_engagement_patterns(insights),
            "recommendations": _generate_memory_recommendations(insights)
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting memory analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


def _analyze_engagement_patterns(insights: List[MemoryInsight]) -> Dict[str, Any]:
    """Analyze user engagement patterns from insights."""
    if not insights:
        return {"pattern": "insufficient_data"}
    
    # Calculate average frequency
    avg_frequency = sum(insight.frequency for insight in insights) / len(insights)
    
    # Identify dominant topics
    topic_frequencies = {}
    for insight in insights:
        topic_frequencies[insight.topic] = insight.frequency
    
    # Determine engagement pattern
    if avg_frequency > 5:
        pattern = "highly_engaged"
    elif avg_frequency > 3:
        pattern = "moderately_engaged"
    else:
        pattern = "casual_user"
    
    return {
        "pattern": pattern,
        "average_topic_frequency": avg_frequency,
        "dominant_topics": list(topic_frequencies.keys())[:3],
        "topic_distribution": topic_frequencies
    }


def _generate_memory_recommendations(insights: List[MemoryInsight]) -> List[str]:
    """Generate recommendations based on memory insights."""
    recommendations = []
    
    if not insights:
        return ["Continue engaging with the AI assistant to build conversation history"]
    
    # Analyze top topics
    top_topics = [insight.topic for insight in insights[:3]]
    
    if "coffee" in top_topics:
        recommendations.append("Consider exploring advanced coffee processing techniques")
    
    if "pests" in top_topics:
        recommendations.append("Review integrated pest management strategies")
    
    if "market" in top_topics:
        recommendations.append("Stay updated on coffee market trends and pricing")
    
    # Check for recent activity
    recent_insights = [i for i in insights if (datetime.utcnow() - i.last_mentioned).days < 7]
    if recent_insights:
        recommendations.append("Continue exploring your current farming interests")
    else:
        recommendations.append("Consider asking about seasonal farming activities")
    
    return recommendations[:3]  # Limit to top 3 recommendations


@router.post("/auto-consolidate")
async def auto_consolidate_sessions():
    """
    Automatically consolidate old conversation sessions.
    This endpoint can be called periodically to maintain memory efficiency.
    """
    try:
        # This would typically be run as a background task
        # For now, we'll just return a placeholder response
        
        logger.info("Auto-consolidation endpoint called")
        
        return {
            "status": "success",
            "message": "Auto-consolidation process initiated",
            "note": "This feature will be implemented as a background task"
        }
        
    except Exception as e:
        logger.error(f"Error in auto-consolidation: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-consolidation failed: {str(e)}")


# Add necessary imports for recommendations
from datetime import datetime
