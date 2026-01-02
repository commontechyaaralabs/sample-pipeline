"""
BigQuery repository implementation using Application Default Credentials.

This module connects to BigQuery using Google Cloud's Application Default
Credentials (ADC). No credentials are stored in code or environment variables.

Authentication is handled by:
- Cloud Run: Attached service account
- GKE: Workload Identity
- GCE: VM service account
- Local: gcloud auth application-default login

⚠️ NO SERVICE ACCOUNT KEYS. NO ENV VARS. NO SECRETS.
"""
from typing import List, Dict, Any
from google.cloud import bigquery
import os

# Initialize BigQuery client using Application Default Credentials
# This will automatically use:
# 1. Service account attached to Cloud Run/GKE/GCE
# 2. User credentials from gcloud CLI (local dev)
# 3. Environment variable GOOGLE_APPLICATION_CREDENTIALS (if set, but we don't use this)
client = bigquery.Client()

# These should be set via environment variables at deployment time
# Format: project.dataset.view_name
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "your-dataset")
THREAD_LIST_VIEW = os.getenv("BIGQUERY_THREAD_LIST_VIEW", "v_thread_list")
MONTHLY_AGGREGATES_VIEW = os.getenv("BIGQUERY_MONTHLY_AGGREGATES_VIEW", "v_monthly_thread_aggregates")


def _get_view_name(view_name: str) -> str:
    """Construct fully qualified BigQuery view name."""
    return f"`{PROJECT_ID}.{DATASET_ID}.{view_name}`"


def get_threads(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve threads from BigQuery v_thread_list view.
    
    Uses parameterized queries to prevent SQL injection.
    Returns data matching the mock repository structure.
    """
    query = f"""
    SELECT *
    FROM {_get_view_name(THREAD_LIST_VIEW)}
    ORDER BY last_message_ts DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    
    job = client.query(query, job_config=job_config)
    results = job.result()
    
    # Convert BigQuery Row objects to dictionaries
    return [dict(row) for row in results]


def get_monthly_aggregates(months: int) -> List[Dict[str, Any]]:
    """
    Retrieve monthly aggregates from BigQuery v_monthly_thread_aggregates view.
    
    Uses parameterized queries to prevent SQL injection.
    Returns data matching the mock repository structure.
    """
    query = f"""
    SELECT *
    FROM {_get_view_name(MONTHLY_AGGREGATES_VIEW)}
    ORDER BY month DESC
    LIMIT @months
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("months", "INT64", months)
        ]
    )
    
    job = client.query(query, job_config=job_config)
    results = job.result()
    
    # Convert BigQuery Row objects to dictionaries
    return [dict(row) for row in results]

