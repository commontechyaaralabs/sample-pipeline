-- View: v_thread_state_final
-- Purpose: Final explainable thread state view with LLM values or heuristic fallback
-- Source: thread_state (heuristic) + thread_state_explain (LLM) + message_sentiment
-- Project: clariversev1
-- Dataset: flipkart_slices

CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_thread_state_final` AS
WITH thread_base AS (
  SELECT
    thread_id,
    last_message_ts,
    message_count,
    thread_status AS heuristic_thread_status
  FROM `clariversev1.flipkart_slices.thread_state`
  WHERE thread_id IS NOT NULL
),
latest_explain AS (
  SELECT
    thread_id,
    ARRAY_AGG(
      STRUCT(
        thread_status,
        next_action_owner,
        status_reason,
        confidence,
        created_at
      )
      ORDER BY created_at DESC
      LIMIT 1
    )[OFFSET(0)] AS explain
  FROM `clariversev1.flipkart_slices.thread_state_explain`
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
  tb.thread_id,
  -- Use LLM thread_status if available, otherwise fallback to heuristic
  COALESCE(le.explain.thread_status, tb.heuristic_thread_status) AS thread_status,
  -- next_action_owner only comes from LLM (NULL if not available)
  le.explain.next_action_owner AS next_action_owner,
  -- status_reason only comes from LLM (NULL if not available)
  le.explain.status_reason AS status_reason,
  -- status confidence only comes from LLM (NULL if not available)
  le.explain.confidence AS status_confidence,
  -- source indicator: "llm" if explain exists, "heuristic" otherwise
  CASE 
    WHEN le.explain.thread_status IS NOT NULL THEN 'llm'
    ELSE 'heuristic'
  END AS source,
  -- Sentiment fields from message_sentiment
  sl.sentiment_label AS sentiment,
  sl.sentiment_struct.confidence AS confidence,
  sl.sentiment_struct.prompt_version AS prompt_version,
  sl.sentiment_struct.model_name AS model_name,
  tb.last_message_ts,
  tb.message_count
FROM thread_base tb
LEFT JOIN latest_explain le
  USING (thread_id)
LEFT JOIN sentiment_labeled sl
  USING (thread_id)
ORDER BY tb.last_message_ts DESC;

