# Memory Intelligence Configuration
# Enhanced memory management settings for Guka AI Agent

# Memory Intelligence Settings
MEMORY_INTELLIGENCE_ENABLED = True

# Relevance Scoring Weights
RELEVANCE_WEIGHTS = {
    "semantic_similarity": 0.4,
    "recency_score": 0.15,
    "frequency_score": 0.1,
    "topic_alignment": 0.2,
    "context_continuity": 0.15
}

# Memory Insights Settings
INSIGHTS_MIN_FREQUENCY = 2
INSIGHTS_MAX_RESULTS = 5
INSIGHTS_ANALYSIS_DAYS = 30

# Memory Context Settings
MAX_MEMORIES_PER_CONTEXT = 5
MEMORY_CONFIDENCE_THRESHOLD = 0.6
HIGH_RELEVANCE_THRESHOLD = 0.8

# Conversation Summarization
AUTO_CONSOLIDATE_AFTER_HOURS = 24
MIN_MESSAGES_FOR_SUMMARY = 3
SUMMARY_MAX_LENGTH = 500

# Farming Topic Keywords
FARMING_TOPICS = {
    "coffee": ["coffee", "arabica", "robusta", "sl28", "sl34", "ruiru", "batian", "k7"],
    "pests": ["cbd", "clr", "thrips", "mites", "aphids", "pests", "disease", "fungus"],
    "weather": ["rain", "drought", "weather", "season", "climate", "temperature"],
    "harvest": ["harvest", "picking", "processing", "drying", "milling", "pulping"],
    "planting": ["planting", "seedlings", "nursery", "spacing", "transplanting"],
    "soil": ["soil", "fertilizer", "nutrition", "ph", "organic", "compost", "manure"],
    "market": ["price", "market", "selling", "buyer", "cooperative", "auction", "grade"],
    "quality": ["quality", "grade", "aa", "ab", "screening", "defects", "cupping"]
}

# Memory Cleanup Settings
CLEANUP_OLD_MEMORIES_DAYS = 365
CLEANUP_LOW_RELEVANCE_THRESHOLD = 0.3
BATCH_PROCESSING_SIZE = 100
