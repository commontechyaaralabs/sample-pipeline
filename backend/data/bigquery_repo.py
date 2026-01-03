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

# These should be set via environment variables at deployment time
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "clariversev1")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "flipkart_slices")

# Initialize BigQuery client using Application Default Credentials
# This will automatically use:
# 1. Service account attached to Cloud Run/GKE/GCE
# 2. User credentials from gcloud CLI (local dev)
# 3. Environment variable GOOGLE_APPLICATION_CREDENTIALS (if set, but we don't use this)
# Pass project ID to avoid initialization errors
try:
    client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"WARNING: Failed to initialize BigQuery client: {e}")
    print(f"Make sure you have authenticated: gcloud auth application-default login")
    client = None  # Will fail on first query, but at least server starts
THREAD_LIST_VIEW = os.getenv("BIGQUERY_THREAD_LIST_VIEW", "v_thread_state_final")
MONTHLY_AGGREGATES_VIEW = os.getenv("BIGQUERY_MONTHLY_AGGREGATES_VIEW", "v_monthly_thread_aggregates")

# Table names (fallback if views don't exist)
# Default to the actual tables: clariversev1.flipkart_slices.*
EMAIL_RAW_TABLE = os.getenv("BIGQUERY_EMAIL_RAW_TABLE", "interaction_event")
THREAD_STATE_TABLE = os.getenv("BIGQUERY_THREAD_STATE_TABLE", "thread_state")
MESSAGE_SENTIMENT_TABLE = os.getenv("BIGQUERY_MESSAGE_SENTIMENT_TABLE", "message_sentiment")

# Whether to use views (preferred) or direct table queries
USE_VIEWS = os.getenv("BIGQUERY_USE_VIEWS", "true").lower() == "true"


def _get_table_name(table_name: str) -> str:
    """Construct fully qualified BigQuery table/view name."""
    return f"`{PROJECT_ID}.{DATASET_ID}.{table_name}`"


def get_threads(limit: int) -> List[Dict[str, Any]]:
    """
    Retrieve threads from BigQuery.
    
    Uses views if available, otherwise queries tables directly.
    Uses parameterized queries to prevent SQL injection.
    Returns thread data with sentiment information.
    """
    if USE_VIEWS:
        # Use view (preferred - faster and cleaner)
        query = f"""
        SELECT *
        FROM {_get_table_name(THREAD_LIST_VIEW)}
        ORDER BY last_message_ts DESC
        LIMIT @limit
        """
    else:
        # Direct table query (fallback if views don't exist)
        # Uses materialized thread_state table + thread_state_explain + message_sentiment
        query = f"""
        WITH thread_summary AS (
          SELECT
            thread_id,
            last_message_ts,
            message_count,
            thread_status
          FROM {_get_table_name(THREAD_STATE_TABLE)}
          WHERE thread_id IS NOT NULL
        ),
        latest_sentiment AS (
          SELECT
            thread_id,
            ARRAY_AGG(
              STRUCT(
                sentiment,
                confidence,
                prompt_version,
                model_name,
                created_at
              )
              ORDER BY created_at DESC
              LIMIT 1
            )[OFFSET(0)] AS s
          FROM {_get_table_name(MESSAGE_SENTIMENT_TABLE)}
          WHERE thread_id IS NOT NULL
          GROUP BY thread_id
        ),
        latest_explain AS (
          SELECT
            thread_id,
            ARRAY_AGG(
              STRUCT(
                thread_status AS explain_thread_status,
                next_action_owner,
                status_reason,
                confidence AS status_confidence,
                prompt_version AS explain_prompt_version,
                model_name AS explain_model_name,
                created_at
              )
              ORDER BY created_at DESC
              LIMIT 1
            )[OFFSET(0)] AS e
          FROM `{PROJECT_ID}.{DATASET_ID}.thread_state_explain`
          WHERE thread_id IS NOT NULL
          GROUP BY thread_id
        )
        SELECT
          t.thread_id,
          t.last_message_ts,
          t.message_count,
          COALESCE(e.explain_thread_status, t.thread_status) AS thread_status,
          s.sentiment,
          s.confidence,
          s.prompt_version,
          s.model_name,
          e.next_action_owner,
          e.status_reason,
          CASE WHEN e.thread_id IS NOT NULL THEN 'llm' ELSE 'heuristic' END AS status_source,
          e.status_confidence
        FROM thread_summary t
        LEFT JOIN latest_sentiment s
          USING (thread_id)
        LEFT JOIN latest_explain e
          USING (thread_id)
        ORDER BY t.last_message_ts DESC
        LIMIT @limit
        """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    
    try:
        job = client.query(query, job_config=job_config)
        results = job.result()
        
        # Convert BigQuery Row objects to dictionaries
        return [dict(row) for row in results]
    except Exception as e:
        # Log detailed error for debugging
        error_msg = str(e)
        print(f"ERROR in get_threads:")
        print(f"  Project: {PROJECT_ID}, Dataset: {DATASET_ID}")
        print(f"  Using views: {USE_VIEWS}")
        print(f"  Error: {error_msg}")
        if "Not found" in error_msg or "does not exist" in error_msg:
            raise Exception(f"Table or view not found. Backend team needs to create: {THREAD_STATE_TABLE if not USE_VIEWS else THREAD_LIST_VIEW}")
        raise Exception(f"BigQuery error: {error_msg}")


def get_monthly_aggregates(months: int) -> List[Dict[str, Any]]:
    """
    Retrieve monthly aggregates from BigQuery.
    
    Uses views if available, otherwise queries tables directly.
    Uses parameterized queries to prevent SQL injection.
    Returns monthly thread aggregates with sentiment distribution.
    """
    if USE_VIEWS:
        # Use view (preferred - faster and cleaner)
        query = f"""
        SELECT *
        FROM {_get_table_name(MONTHLY_AGGREGATES_VIEW)}
        ORDER BY month DESC
        LIMIT @months
        """
    else:
        # Direct table query (fallback if views don't exist)
        # Uses materialized thread_state table
        query = f"""
        WITH thread_summary AS (
          SELECT
            thread_id,
            last_message_ts
          FROM {_get_table_name(THREAD_STATE_TABLE)}
          WHERE thread_id IS NOT NULL
        ),
        latest_sentiment AS (
          SELECT
            thread_id,
            ARRAY_AGG(sentiment ORDER BY created_at DESC LIMIT 1)[OFFSET(0)] AS sentiment
          FROM {_get_table_name(MESSAGE_SENTIMENT_TABLE)}
          WHERE thread_id IS NOT NULL
          GROUP BY thread_id
        )
        SELECT
          FORMAT_TIMESTAMP('%Y-%m', t.last_message_ts) AS month,
          COUNT(*) AS thread_count,
          COUNTIF(s.sentiment = 'pos') AS pos_threads,
          COUNTIF(s.sentiment = 'neutral') AS neutral_threads,
          COUNTIF(s.sentiment = 'neg') AS neg_threads
        FROM thread_summary t
        LEFT JOIN latest_sentiment s
          USING (thread_id)
        GROUP BY month
        ORDER BY month DESC
        LIMIT @months
        """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("months", "INT64", months)
        ]
    )
    
    if client is None:
        raise Exception("BigQuery client not initialized. Run: gcloud auth application-default login")
    
    try:
        job = client.query(query, job_config=job_config)
        results = job.result()
        
        # Convert BigQuery Row objects to dictionaries
        return [dict(row) for row in results]
    except Exception as e:
        # Log detailed error for debugging
        error_msg = str(e)
        print(f"ERROR in get_monthly_aggregates:")
        print(f"  Project: {PROJECT_ID}, Dataset: {DATASET_ID}")
        print(f"  Using views: {USE_VIEWS}")
        print(f"  Error: {error_msg}")
        if "Not found" in error_msg or "does not exist" in error_msg or "404" in error_msg:
            missing = MONTHLY_AGGREGATES_VIEW if USE_VIEWS else THREAD_STATE_TABLE
            raise Exception(f"Table/view not found: {PROJECT_ID}.{DATASET_ID}.{missing}. Backend team needs to create this.")
        if "403" in error_msg or "permission" in error_msg.lower():
            raise Exception(f"Permission denied. Check BigQuery access for project {PROJECT_ID}")
        raise Exception(f"BigQuery error: {error_msg}")

