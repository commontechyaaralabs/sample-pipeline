"""
FastAPI routes for thread data endpoints.

These endpoints provide the contract between frontend and backend.
All data access is delegated to the repository layer.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

# Import BigQuery repository functions
from data.bigquery_repo import get_threads, get_monthly_aggregates

router = APIRouter()


@router.get("/threads")
async def list_threads(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Retrieve a list of threads from v_thread_state_final view.
    
    Args:
        limit: Maximum number of threads to return (default: 200, max: 200)
        
    Returns:
        List of thread objects with fields:
        - thread_id, last_message_ts, message_count, thread_status
        - sentiment, confidence, prompt_version, model_name
        - next_action_owner, status_reason, status_source, status_confidence (if LLM explanation available)
    """
    try:
        if limit < 1 or limit > 200:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 200"
            )
        return get_threads(limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving threads: {str(e)}"
        )


@router.get("/threads/aggregates/monthly")
async def get_monthly_aggregates_endpoint(months: int = 6) -> List[Dict[str, Any]]:
    """
    Retrieve monthly thread aggregates.
    
    Args:
        months: Number of months to retrieve (default: 6)
        
    Returns:
        List of monthly aggregate objects
    """
    try:
        if months < 1 or months > 24:
            raise HTTPException(
                status_code=400,
                detail="Months must be between 1 and 24"
            )
        return get_monthly_aggregates(months)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving monthly aggregates: {str(e)}"
        )

