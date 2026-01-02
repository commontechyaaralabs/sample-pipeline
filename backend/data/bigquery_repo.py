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
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "clariversev1")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "flipkart_slices")
THREAD_LIST_VIEW = os.getenv("BIGQUERY_THREAD_LIST_VIEW", "v_thread_list")
MONTHLY_AGGREGATES_VIEW = os.getenv("BIGQUERY_MONTHLY_AGGREGATES_VIEW", "v_monthly_thread_aggregates")

# Table names (fallback if views don't exist)
# Default to the actual table: clariversev1.flipkart_slices.interaction_event
EMAIL_RAW_TABLE = os.getenv("BIGQUERY_EMAIL_RAW_TABLE", "interaction_event")
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
    Returns data matching the mock repository structure.
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
        # Works with email_raw_slice_001 table structure
        query = f"""
        WITH thread_summary AS (
          SELECT
            thread_id,
            MAX(thread_last_message_at) AS last_message_ts,
            MAX(thread_message_count) AS message_count,
            CASE 
              WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(thread_last_message_at), DAY) <= 7 
              THEN 'open'
              ELSE 'closed'
            END AS thread_status
          FROM {_get_table_name(EMAIL_RAW_TABLE)}
          WHERE thread_id IS NOT NULL
          GROUP BY thread_id
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
        )
        SELECT
          t.thread_id,
          t.last_message_ts,
          t.message_count,
          t.thread_status,
          s.sentiment,
          s.confidence,
          s.prompt_version,
          s.model_name
        FROM thread_summary t
        LEFT JOIN latest_sentiment s
          USING (thread_id)
        ORDER BY t.last_message_ts DESC
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
    Retrieve monthly aggregates from BigQuery.
    
    Uses views if available, otherwise queries tables directly.
    Uses parameterized queries to prevent SQL injection.
    Returns data matching the mock repository structure.
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
        # Works with email_raw_slice_001 table structure
        query = f"""
        WITH thread_summary AS (
          SELECT
            thread_id,
            MAX(thread_last_message_at) AS last_message_ts
          FROM {_get_table_name(EMAIL_RAW_TABLE)}
          WHERE thread_id IS NOT NULL
          GROUP BY thread_id
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
    
    job = client.query(query, job_config=job_config)
    results = job.result()
    
    # Convert BigQuery Row objects to dictionaries
    return [dict(row) for row in results]

