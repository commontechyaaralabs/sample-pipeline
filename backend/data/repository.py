"""
Repository interface for thread data access.

This module defines the contract that all data repositories must implement.
No credentials or implementation details here - just the interface.
"""
from typing import List, Dict, Any


def get_threads(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve a list of threads ordered by last message timestamp.
    
    Args:
        limit: Maximum number of threads to return
        
    Returns:
        List of thread dictionaries with fields:
        - thread_id: str
        - last_message_ts: str (ISO format)
        - message_count: int
        - thread_status: str
        - sentiment: str
        - confidence: float
        - prompt_version: str
        - model_name: str
    """
    raise NotImplementedError("Subclasses must implement get_threads")


def get_monthly_aggregates(months: int) -> List[Dict[str, Any]]:
    """
    Retrieve monthly thread aggregates.
    
    Args:
        months: Number of months to retrieve (ordered DESC)
        
    Returns:
        List of monthly aggregate dictionaries with fields:
        - month: str (YYYY-MM format)
        - thread_count: int
        - pos_threads: int
        - neutral_threads: int
        - neg_threads: int
    """
    raise NotImplementedError("Subclasses must implement get_monthly_aggregates")

