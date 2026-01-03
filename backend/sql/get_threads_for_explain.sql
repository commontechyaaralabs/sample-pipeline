-- Query: get_threads_for_explain
-- Purpose: Get thread status and last 2 messages for explanation generation
-- Returns: thread_id, thread_status, last_message_body, previous_message_body
-- Limits: 50 threads
-- 
WITH thread_statuses AS (
  SELECT
    thread_id,
    thread_status
  FROM `clariversev1.flipkart_slices.thread_state`
  WHERE thread_id IS NOT NULL
),
recent_messages AS (
  SELECT
    ie.thread_id,
    ts.thread_status,
    ARRAY_AGG(
      STRUCT(
        ie.body_text AS message_body,
        ie.event_ts
      )
      ORDER BY ie.event_ts DESC
      LIMIT 2
    ) AS messages
  FROM thread_statuses ts
  INNER JOIN `clariversev1.flipkart_slices.interaction_event` ie
    ON ts.thread_id = ie.thread_id
  WHERE ie.thread_id IS NOT NULL
  GROUP BY ie.thread_id, ts.thread_status
)
SELECT
  thread_id,
  thread_status,
  messages[OFFSET(0)].message_body AS last_message_body,
  CASE 
    WHEN ARRAY_LENGTH(messages) > 1 THEN messages[OFFSET(1)].message_body
    ELSE NULL
  END AS previous_message_body
FROM recent_messages
ORDER BY thread_id
LIMIT 50;

