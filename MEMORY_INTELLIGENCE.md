# 🧠 Memory Intelligence System

Advanced memory management for Guka AI Agent with intelligent context retrieval, automatic summarization, and pattern analysis.

## 🌟 Features

### 1. **Enhanced Memory Retrieval**
- **Multi-factor Relevance Scoring**: Combines semantic similarity, recency, topic alignment, and context continuity
- **Intelligent Memory Classification**: Automatically categorizes memories by type (questions, problems, market inquiries, etc.)
- **Context-Aware Filtering**: Filters memories based on conversation flow and farming context

### 2. **Memory Insights Generation**
- **Pattern Recognition**: Automatically identifies recurring topics and farming interests
- **Importance Scoring**: Calculates importance based on frequency, recency, and consistency
- **Trend Analysis**: Tracks changes in farming focus and concerns over time

### 3. **Conversation Summarization**
- **Session Consolidation**: Automatically summarizes conversation sessions
- **Key Topic Extraction**: Identifies main farming topics discussed
- **Action Item Detection**: Extracts specific farming tasks and recommendations
- **Emotional Tone Analysis**: Understands farmer sentiment and engagement

### 4. **Smart Context Building**
- **Relevance-Based Selection**: Chooses most relevant memories for current context
- **Insight Integration**: Incorporates historical patterns into responses
- **Confidence Scoring**: Provides confidence metrics for memory relevance

## 🚀 API Endpoints

### Memory Insights
```
GET /api/memory-intelligence/insights/{user_id}
```
Get intelligent insights from user's conversation history.

**Parameters:**
- `user_id`: User identifier
- `limit`: Maximum insights to return (default: 5)
- `min_frequency`: Minimum topic frequency (default: 2)

**Response:**
```json
{
  "insights": [
    {
      "topic": "coffee",
      "summary": "User frequently asks about coffee disease management",
      "importance_score": 0.85,
      "frequency": 5,
      "first_mentioned": "2024-01-15T10:30:00Z",
      "last_mentioned": "2024-01-20T14:20:00Z"
    }
  ]
}
```

### Intelligent Context
```
GET /api/memory-intelligence/context/{user_id}
```
Get enhanced memory context for a specific query.

**Parameters:**
- `user_id`: User identifier
- `query`: Current user query
- `max_memories`: Maximum memories to return (default: 5)
- `include_insights`: Include extracted insights (default: true)

**Response:**
```json
{
  "relevant_memories": [...],
  "memory_insights": [...],
  "context_summary": "Recent conversations about coffee disease and harvest timing",
  "confidence_score": 0.82
}
```

### Session Consolidation
```
POST /api/memory-intelligence/consolidate/{session_id}
```
Consolidate a conversation session into a summary.

**Parameters:**
- `session_id`: Session to consolidate
- `user_id`: User identifier

**Response:**
```json
{
  "session_id": "session_123",
  "summary": "Discussion about coffee berry disease treatment options",
  "key_topics": ["coffee", "pests", "treatment"],
  "action_items": ["Apply copper fungicide", "Monitor weather conditions"],
  "farming_insights": ["Early detection is crucial for CBD management"],
  "emotional_tone": "concerned but engaged",
  "message_count": 8,
  "duration_minutes": 15
}
```

### Memory Analysis
```
GET /api/memory-intelligence/analysis/{user_id}
```
Get comprehensive memory analysis for a user.

**Response:**
```json
{
  "user_id": "farmer_123",
  "analysis_period_days": 30,
  "total_insights": 7,
  "top_topics": ["coffee", "pests", "market"],
  "engagement_patterns": {
    "pattern": "highly_engaged",
    "average_topic_frequency": 4.2,
    "dominant_topics": ["coffee", "pests", "harvest"]
  },
  "recommendations": [
    "Consider exploring advanced coffee processing techniques",
    "Review integrated pest management strategies"
  ]
}
```

## 🔧 Technical Implementation

### Memory Intelligence Service
The core service (`MemoryIntelligenceService`) provides:

1. **Enhanced Relevance Calculation**
   - Semantic similarity using vector embeddings
   - Recency scoring (decay over time)
   - Topic alignment with current query
   - Context continuity analysis

2. **Pattern Analysis**
   - Topic frequency tracking
   - Conversation threading
   - Engagement pattern recognition
   - Trend identification

3. **Intelligent Summarization**
   - LLM-powered conversation summaries
   - Key entity extraction
   - Action item identification
   - Sentiment analysis

### Integration with Agent Service
The enhanced memory system integrates seamlessly with the existing agent:

```python
# Enhanced memory context retrieval
intelligent_context = await memory_intelligence_service.get_intelligent_memory_context(
    query=request.message,
    user_id=request.user_id,
    max_memories=5,
    include_insights=True
)

# Build enhanced memory context
enhanced_memory_context = self._build_intelligent_memory_context(
    relevant_memories, memory_insights, context_summary
)
```

## 📊 Relevance Scoring Algorithm

The system uses a weighted scoring algorithm:

```
Total Score = (
    semantic_similarity × 0.4 +
    recency_score × 0.15 +
    frequency_score × 0.1 +
    topic_alignment × 0.2 +
    context_continuity × 0.15
)
```

### Scoring Factors:

1. **Semantic Similarity** (40%): Vector similarity between query and memory
2. **Recency Score** (15%): How recently the memory was created (30-day decay)
3. **Frequency Score** (10%): How often the topic appears in conversations
4. **Topic Alignment** (20%): Overlap between farming topics in query and memory
5. **Context Continuity** (15%): Relationship to current conversation thread

## 🎯 Memory Classification

Memories are automatically classified into types:

- **`question`**: User questions and inquiries
- **`problem_solving`**: Issues and troubleshooting discussions
- **`positive_feedback`**: Thanks and positive responses
- **`market_inquiry`**: Pricing and market-related queries
- **`farming_activity`**: Specific farming tasks and activities
- **`general_conversation`**: General farming discussions

## 🔍 Entity Extraction

The system extracts key farming entities:

### Coffee Varieties
- SL28, SL34, Ruiru 11, Batian, K7

### Locations
- Kenyan counties (Nyeri, Kiambu, Muranga, etc.)

### Time References
- Today, yesterday, week, month, season, harvest time

### Farming Context
- Crop mentions
- Activity types (planting, harvesting, pruning)
- Problem indicators
- Season references

## 🧪 Testing

Run the memory intelligence test suite:

```bash
python test_memory_intelligence.py
```

This will test:
- Memory context retrieval
- Relevance scoring
- Insight extraction
- Memory classification
- Entity extraction

## ⚙️ Configuration

Memory intelligence settings can be configured in `memory_intelligence_config.py`:

```python
# Relevance scoring weights
RELEVANCE_WEIGHTS = {
    "semantic_similarity": 0.4,
    "recency_score": 0.15,
    "topic_alignment": 0.2,
    # ...
}

# Memory insights settings
INSIGHTS_MIN_FREQUENCY = 2
INSIGHTS_MAX_RESULTS = 5
INSIGHTS_ANALYSIS_DAYS = 30
```

## 🚀 Future Enhancements

### Planned Features:
1. **Proactive Memory Triggers**: Automatic reminders based on farming cycles
2. **Cross-User Knowledge Synthesis**: Anonymous pattern sharing across farmers
3. **Predictive Insights**: Forecast farming needs based on historical patterns
4. **Memory Visualization**: Dashboard showing memory patterns and insights
5. **Automated Memory Cleanup**: Intelligent archiving of old, low-relevance memories

### Advanced Memory Features:
- **Hierarchical Memory Organization**: Topic-based memory clustering
- **Temporal Memory Mapping**: Time-based memory organization
- **Emotional Memory Weighting**: Factor in emotional context for relevance
- **Multi-Modal Memory**: Integration with image and audio memories

## 📈 Performance Metrics

The system tracks:
- **Memory Retrieval Accuracy**: Relevance of retrieved memories
- **Context Confidence**: System confidence in memory context
- **Insight Quality**: Usefulness of extracted insights
- **Processing Speed**: Time to retrieve and enhance memories

## 🔒 Privacy & Security

- **User Isolation**: Memories are strictly isolated by user ID
- **Data Anonymization**: Insights can be anonymized for research
- **Retention Policies**: Configurable memory retention periods
- **Access Control**: API endpoints respect user permissions

---

## 🎉 Getting Started

1. **Enable Memory Intelligence** in your agent configuration
2. **Initialize the service** in your application startup
3. **Use enhanced memory context** in your chat processing
4. **Monitor insights** through the API endpoints
5. **Configure settings** based on your farming domain needs

The Memory Intelligence system transforms your AI agent from a simple chat bot into a truly intelligent farming assistant that learns and adapts to each farmer's unique needs and patterns.

**Happy Farming! 🌱**
