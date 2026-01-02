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
    Generates up to 200 threads for realistic testing.
    """
    base_time = datetime.utcnow()
    threads = []
    max_threads = min(limit, 200)
    
    for i in range(max_threads):
        # Vary timestamps more realistically (hours, days, weeks)
        if i < 50:
            thread_time = base_time - timedelta(hours=i)
        elif i < 150:
            thread_time = base_time - timedelta(days=(i - 50) // 2)
        else:
            thread_time = base_time - timedelta(weeks=(i - 150) // 10)
        
        sentiment_options = ["pos", "neg", "neutral"]
        sentiment = sentiment_options[i % 3]
        
        # Vary confidence more realistically
        confidence_base = 0.65 + (i % 5) * 0.05
        confidence = round(confidence_base + (0.1 if sentiment == "pos" else -0.05), 2)
        
        threads.append({
            "thread_id": f"t-{str(i+1).zfill(6)}",
            "last_message_ts": thread_time.isoformat(),
            "message_count": (i % 20) + 1,
            "thread_status": "open" if i % 4 != 0 else "closed",
            "sentiment": sentiment,
            "confidence": confidence,
            "prompt_version": f"v0.{(i % 3) + 1}",
            "model_name": "gemini" if i % 2 == 0 else "gpt-4"
        })
    
    return threads


def get_monthly_aggregates(months: int) -> List[Dict[str, Any]]:
    """
    Return mock monthly aggregate data matching the v_monthly_thread_aggregates view structure.
    Returns in descending order (newest first) to match BigQuery.
    """
    base_date = datetime.utcnow().replace(day=1)
    aggregates = []
    
    for i in range(months):
        # Calculate month going backwards from current
        month_date = base_date - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m")
        
        # Generate realistic-looking data with some variation
        base_count = 120 + (i * 8) + (i % 3) * 5
        # Vary sentiment distribution slightly
        pos_ratio = 0.45 + (i % 5) * 0.02
        neutral_ratio = 0.30 + (i % 3) * 0.01
        
        pos_threads = int(base_count * pos_ratio)
        neutral_threads = int(base_count * neutral_ratio)
        neg_threads = base_count - pos_threads - neutral_threads
        
        aggregates.append({
            "month": month_str,
            "thread_count": base_count,
            "pos_threads": pos_threads,
            "neutral_threads": neutral_threads,
            "neg_threads": neg_threads
        })
    
    # Return in descending order (newest first) to match BigQuery
    return list(reversed(aggregates))

