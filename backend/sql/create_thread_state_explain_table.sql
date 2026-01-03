-- Create table: thread_state_explain
-- Purpose: Store thread state explanations with partitioning and clustering for optimal performance
-- Project: clariversev1
-- Dataset: flipkart_slices

CREATE TABLE IF NOT EXISTS `clariversev1.flipkart_slices.thread_state_explain` (
  thread_id STRING NOT NULL,
  thread_status STRING,
  next_action_owner STRING,
  status_reason STRING,
  confidence FLOAT64,
  prompt_version STRING,
  model_name STRING,
  created_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(created_at)
CLUSTER BY thread_id
OPTIONS(
  description = 'Thread state explanations table partitioned by date and clustered by thread_id for efficient querying'
);

