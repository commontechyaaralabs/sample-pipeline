-- BigQuery Views for Thread Analytics
-- Run these in BigQuery to create the views that the backend will query
-- Replace PROJECT_ID, DATASET_ID, and TABLE_NAME with your actual values
-- Example: clariversev1.flipkart_slices.interaction_event

-- View: v_thread_list
-- Purpose: Thread list with latest sentiment per thread
-- Source: interaction_event (one row per message, grouped by thread_id)
CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.v_thread_list` AS
WITH thread_summary AS (
  SELECT
    thread_id,
    MAX(thread_last_message_at) AS last_message_ts,
    MAX(thread_message_count) AS message_count,
    -- Derive thread_status: if last message is recent (within 7 days), consider open
    CASE 
      WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(thread_last_message_at), DAY) <= 7 
      THEN 'open'
      ELSE 'closed'
    END AS thread_status
  FROM `PROJECT_ID.DATASET_ID.TABLE_NAME`
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
  FROM `PROJECT_ID.DATASET_ID.message_sentiment`
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
ORDER BY t.last_message_ts DESC;

-- View: v_monthly_thread_aggregates
-- Purpose: Monthly aggregates with sentiment distribution
-- Source: interaction_event (one row per message, grouped by thread_id)
CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.v_monthly_thread_aggregates` AS
WITH thread_summary AS (
  SELECT
    thread_id,
    MAX(thread_last_message_at) AS last_message_ts
  FROM `PROJECT_ID.DATASET_ID.TABLE_NAME`
  WHERE thread_id IS NOT NULL
  GROUP BY thread_id
),
latest_sentiment AS (
  SELECT
    thread_id,
    ARRAY_AGG(sentiment ORDER BY created_at DESC LIMIT 1)[OFFSET(0)] AS sentiment
  FROM `PROJECT_ID.DATASET_ID.message_sentiment`
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
ORDER BY month DESC;

