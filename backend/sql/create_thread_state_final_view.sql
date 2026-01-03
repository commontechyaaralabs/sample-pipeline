-- View: v_thread_state_final
-- Purpose: Final explainable thread state view with LLM values or heuristic fallback
-- Source: thread_state (heuristic) + thread_state_explain (LLM)
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
)
SELECT
  tb.thread_id,
  -- Use LLM thread_status if available, otherwise fallback to heuristic
  COALESCE(le.explain.thread_status, tb.heuristic_thread_status) AS thread_status,
  -- next_action_owner only comes from LLM (NULL if not available)
  le.explain.next_action_owner AS next_action_owner,
  -- status_reason only comes from LLM (NULL if not available)
  le.explain.status_reason AS status_reason,
  -- confidence only comes from LLM (NULL if not available)
  le.explain.confidence AS confidence,
  -- source indicator: "llm" if explain exists, "heuristic" otherwise
  CASE 
    WHEN le.explain.thread_status IS NOT NULL THEN 'llm'
    ELSE 'heuristic'
  END AS source,
  tb.last_message_ts,
  tb.message_count
FROM thread_base tb
LEFT JOIN latest_explain le
  USING (thread_id)
ORDER BY tb.last_message_ts DESC;

