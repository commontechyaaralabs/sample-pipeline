# BigQuery Views Setup

## Table Structure

Your actual table: `clariversev1.flipkart_slices.interaction_event`

This table has:
- One row per **message** (not per thread)
- Key fields: `thread_id`, `thread_last_message_at`, `thread_message_count`
- Timestamp fields are **TIMESTAMP** type (not strings)

## Creating Views

### Step 1: Update the SQL file

Edit `views.sql` and replace:
- `PROJECT_ID` → `clariversev1`
- `DATASET_ID` → `flipkart_slices`
- `TABLE_NAME` → `interaction_event`

### Step 2: Check for sentiment table

The views assume a `message_sentiment` table exists with:
- `thread_id`
- `sentiment` (pos/neg/neutral)
- `confidence`
- `prompt_version`
- `model_name`
- `created_at`

If this table doesn't exist or has a different name, update the `MESSAGE_SENTIMENT_TABLE` environment variable.

### Step 3: Run the SQL

In BigQuery console, run the updated SQL from `views.sql`:

```sql
-- View: v_thread_list
CREATE OR REPLACE VIEW `clariversev1.flipkart_slices.v_thread_list` AS
-- ... (copy from views.sql with replacements)
```

## Environment Variables

Set these in your backend `.env` or Cloud Run:

```env
GCP_PROJECT_ID=clariversev1
BIGQUERY_DATASET_ID=flipkart_slices
BIGQUERY_EMAIL_RAW_TABLE=interaction_event
BIGQUERY_MESSAGE_SENTIMENT_TABLE=message_sentiment
BIGQUERY_USE_VIEWS=true
```

## Notes

1. **Thread Status**: Derived from `thread_last_message_at` - threads with activity within 7 days are "open", others are "closed"

2. **Timestamp Fields**: The table uses TIMESTAMP type directly, so no parsing is needed

3. **Sentiment Data**: If a thread has no sentiment data, those fields will be NULL (no defaults applied)

4. **Grouping**: Since the table has one row per message, we group by `thread_id` and use `MAX()` to get thread-level aggregates

