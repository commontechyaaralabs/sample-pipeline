"""
FastAPI routes for thread data endpoints.

These endpoints provide the contract between frontend and backend.
All data access is delegated to the repository layer.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os

# Import repository functions based on environment
USE_MOCK = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

if USE_MOCK:
    from data.mock_repo import get_threads, get_monthly_aggregates
else:
    from data.bigquery_repo import get_threads, get_monthly_aggregates

router = APIRouter()


@router.get("/threads")
async def list_threads(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve a list of threads.
    
    Args:
        limit: Maximum number of threads to return (default: 10)
        
    Returns:
        List of thread objects
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
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

