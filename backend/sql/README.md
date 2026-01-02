# BigQuery Views Setup

## Overview

**Backend team creates all tables.** We only create views that join them for the UI.

## Tables (Created by Backend Team)

Backend team will create and populate these tables:

1. **`interaction_event`** - Raw interaction data
   - One row per **message/interaction** (not per thread)
   - Key fields: `thread_id`, `event_ts`, `interaction_id`, `channel`
   - `event_ts` is **TIMESTAMP** type

2. **`thread_state`** - Materialized thread-level intelligence
   - One row per **thread**
   - Fields: `thread_id`, `last_message_ts`, `message_count`, `thread_status`, `computed_at`
   - Populated/updated by backend ingestion process

3. **`message_sentiment`** - LLM sentiment analysis results
   - One row per message per prompt version
   - Fields: `message_id`, `thread_id`, `sentiment`, `confidence`, `prompt_version`, `model_name`, `created_at`

## Creating Views (Our Responsibility)

We create views that join the backend tables for easy UI consumption.

### Step 1: Update the views SQL file

Edit `views.sql` and replace:
- `PROJECT_ID` → `clariversev1`
- `DATASET_ID` → `flipkart_slices`

### Step 2: Run the SQL in BigQuery

In BigQuery console, run the updated SQL from `views.sql`:

```sql
-- View: v_thread_list
CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_thread_list` AS
-- ... (copy from views.sql with replacements)

-- View: v_monthly_thread_aggregates
CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_monthly_thread_aggregates` AS
-- ... (copy from views.sql with replacements)
```

**Note:** These views will work once backend team has created and populated the three tables above.

## Environment Variables

Set these in your backend `.env` or Cloud Run:

```env
GCP_PROJECT_ID=clariversev1
BIGQUERY_DATASET_ID=flipkart_slices
BIGQUERY_EMAIL_RAW_TABLE=interaction_event
BIGQUERY_THREAD_STATE_TABLE=thread_state
BIGQUERY_MESSAGE_SENTIMENT_TABLE=message_sentiment
BIGQUERY_USE_VIEWS=true
```

## Notes

1. **Backend Team Responsibility**: 
   - Creates all three tables (`interaction_event`, `thread_state`, `message_sentiment`)
   - Populates `thread_state` from `interaction_event`
   - Runs LLM sentiment analysis and writes to `message_sentiment`

2. **Our Responsibility**:
   - Create views that join the backend tables
   - Provide API endpoints that query these views
   - Build UI that consumes the API

3. **Thread State**: Read from materialized `thread_state` table (created by backend)
   - Thread status logic: threads with activity within 7 days are "open", others are "closed"

4. **Timestamp Fields**: All tables use TIMESTAMP type directly, so no parsing is needed

5. **Sentiment Data**: If a thread has no sentiment data, those fields will be NULL (no defaults applied)

6. **Views**: Join `thread_state` + `message_sentiment` to provide clean data for UI

