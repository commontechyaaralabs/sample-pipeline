"""
Mock repository for local development and testing.

This module provides mock data that matches the BigQuery view structure.
Used when USE_MOCK_DATA=true (default for local development).
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_threads(limit: int) -> List[Dict[str, Any]]:
    """
    Return mock thread data matching the v_thread_list view structure.
    """
    base_time = datetime.utcnow()
    threads = []
    
    for i in range(min(limit, 20)):  # Generate up to 20 mock threads
        thread_time = base_time - timedelta(hours=i)
        sentiment_options = ["pos", "neg", "neutral"]
        sentiment = sentiment_options[i % 3]
        
        threads.append({
            "thread_id": f"t-{str(i+1).zfill(3)}",
            "last_message_ts": thread_time.isoformat(),
            "message_count": (i + 1) * 2,
            "thread_status": "open" if i % 3 != 0 else "closed",
            "sentiment": sentiment,
            "confidence": round(0.7 + (i % 3) * 0.1, 2),
            "prompt_version": "v0.1",
            "model_name": "gemini"
        })
    
    return threads


def get_monthly_aggregates(months: int) -> List[Dict[str, Any]]:
    """
    Return mock monthly aggregate data matching the v_monthly_thread_aggregates view structure.
    """
    base_date = datetime.utcnow().replace(day=1)
    aggregates = []
    
    for i in range(months):
        month_date = base_date - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")
        
        # Generate realistic-looking data
        thread_count = 100 + (i * 10)
        pos_threads = int(thread_count * 0.5)
        neutral_threads = int(thread_count * 0.3)
        neg_threads = thread_count - pos_threads - neutral_threads
        
        aggregates.append({
            "month": month_str,
            "thread_count": thread_count,
            "pos_threads": pos_threads,
            "neutral_threads": neutral_threads,
            "neg_threads": neg_threads
        })
    
    return aggregates

