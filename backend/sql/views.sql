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
    )[OFFSET(0)] AS sentiment_struct
  FROM `clariversev1.flipkart_slices.message_sentiment`
  WHERE thread_id IS NOT NULL
  GROUP BY thread_id
),
sentiment_labeled AS (
  SELECT
    thread_id,
    sentiment_struct,
    CASE 
      -- Map numeric sentiment values to labels
      WHEN SAFE_CAST(sentiment_struct.sentiment AS INT64) = 1 THEN 'Happy'
      WHEN SAFE_CAST(sentiment_struct.sentiment AS INT64) = 2 THEN 'Bit Irritated'
      WHEN SAFE_CAST(sentiment_struct.sentiment AS INT64) = 3 THEN 'Moderately Concerned'
      WHEN SAFE_CAST(sentiment_struct.sentiment AS INT64) = 4 THEN 'Anger'
      WHEN SAFE_CAST(sentiment_struct.sentiment AS INT64) = 5 THEN 'Frustrated'
      -- Handle string sentiment values (backward compatibility)
      WHEN sentiment_struct.sentiment = 'Happy' OR sentiment_struct.sentiment = 'happy' THEN 'Happy'
      WHEN sentiment_struct.sentiment = 'Bit Irritated' OR sentiment_struct.sentiment = 'bit irritated' THEN 'Bit Irritated'
      WHEN sentiment_struct.sentiment = 'Moderately Concerned' OR sentiment_struct.sentiment = 'moderately concerned' THEN 'Moderately Concerned'
      WHEN sentiment_struct.sentiment = 'Anger' OR sentiment_struct.sentiment = 'anger' THEN 'Anger'
      WHEN sentiment_struct.sentiment = 'Frustrated' OR sentiment_struct.sentiment = 'frustrated' THEN 'Frustrated'
      ELSE CAST(sentiment_struct.sentiment AS STRING)
    END AS sentiment_label
  FROM latest_sentiment
)
SELECT
  t.thread_id,
  t.last_message_ts,
  t.message_count,
  t.thread_status,
  sl.sentiment_label AS sentiment,
  sl.sentiment_struct.confidence AS confidence,
  sl.sentiment_struct.prompt_version AS prompt_version,
  sl.sentiment_struct.model_name AS model_name
FROM thread_summary t
LEFT JOIN sentiment_labeled sl
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
),
sentiment_mapped AS (
  SELECT
    thread_id,
    CASE 
      -- Handle numeric sentiment values (5-point scale)
      -- 1 = Happy
      -- 2 = Bit Irritated
      -- 3 = Moderately Concerned
      -- 4 = Anger
      -- 5 = Frustrated
      WHEN SAFE_CAST(sentiment AS INT64) = 1 THEN 'Happy'
      WHEN SAFE_CAST(sentiment AS INT64) = 2 THEN 'Bit Irritated'
      WHEN SAFE_CAST(sentiment AS INT64) = 3 THEN 'Moderately Concerned'
      WHEN SAFE_CAST(sentiment AS INT64) = 4 THEN 'Anger'
      WHEN SAFE_CAST(sentiment AS INT64) = 5 THEN 'Frustrated'
      -- Handle string sentiment values (backward compatibility)
      WHEN sentiment = 'Happy' OR sentiment = 'happy' THEN 'Happy'
      WHEN sentiment = 'Bit Irritated' OR sentiment = 'bit irritated' THEN 'Bit Irritated'
      WHEN sentiment = 'Moderately Concerned' OR sentiment = 'moderately concerned' THEN 'Moderately Concerned'
      WHEN sentiment = 'Anger' OR sentiment = 'anger' THEN 'Anger'
      WHEN sentiment = 'Frustrated' OR sentiment = 'frustrated' THEN 'Frustrated'
      ELSE NULL
    END AS sentiment_category
  FROM latest_sentiment
)
SELECT
  FORMAT_TIMESTAMP('%Y-%m', t.last_message_ts) AS month,
  COUNT(*) AS thread_count,
  COUNTIF(sm.sentiment_category = 'Happy') AS happy_threads,
  COUNTIF(sm.sentiment_category = 'Bit Irritated') AS bit_irritated_threads,
  COUNTIF(sm.sentiment_category = 'Moderately Concerned') AS moderately_concerned_threads,
  COUNTIF(sm.sentiment_category = 'Anger') AS anger_threads,
  COUNTIF(sm.sentiment_category = 'Frustrated') AS frustrated_threads
FROM thread_summary t
LEFT JOIN sentiment_mapped sm
  USING (thread_id)
GROUP BY month
ORDER BY month DESC;

