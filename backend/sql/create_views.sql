-- BigQuery Views for Thread Analytics
-- Ready to run - Project and Dataset IDs are set
-- Project: clariversev1
-- Dataset: flipkart_slices

-- View: v_thread_list
-- Purpose: Thread list with latest sentiment per thread
-- Source: thread_state (materialized) + message_sentiment
CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_thread_list` AS
WITH thread_summary AS (
  SELECT
    thread_id,
    last_message_ts,
    message_count,
    thread_status
  FROM `clariversev1.flipkart_slices.thread_state`
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
  FROM `clariversev1.flipkart_slices.message_sentiment`
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
-- Source: thread_state (materialized) + message_sentiment
CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_monthly_thread_aggregates` AS
WITH thread_summary AS (
  SELECT
    thread_id,
    last_message_ts
  FROM `clariversev1.flipkart_slices.thread_state`
  WHERE thread_id IS NOT NULL
),
latest_sentiment AS (
  SELECT
    thread_id,
    ARRAY_AGG(sentiment ORDER BY created_at DESC LIMIT 1)[OFFSET(0)] AS sentiment
  FROM `clariversev1.flipkart_slices.message_sentiment`
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


