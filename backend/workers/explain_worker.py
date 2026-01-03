import json
import re
import time
<<<<<<< Updated upstream
=======
import os
import sys
>>>>>>> Stashed changes
from datetime import datetime, timezone
from typing import Dict, Any, List

from google.cloud import bigquery

# Vertex AI (Gemini)
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "clariversev1"
DATASET = "flipkart_slices"
REGION = "us-central1"

PROMPT_VERSION = "thread_state_v0.1"
MODEL_NAME = "gemini-2.0-flash"

<<<<<<< Updated upstream
BATCH_LIMIT = 50  # number of threads to explain per run
=======
# Configurable batch limit - can be set via environment variable or command line arg
BATCH_LIMIT = int(os.getenv("EXPLAIN_BATCH_LIMIT", "50"))
>>>>>>> Stashed changes
MAX_RETRIES = 3


def fetch_threads_to_explain(bq: bigquery.Client) -> List[Dict[str, Any]]:
    """Fetch threads that need explanation (not yet explained with current prompt version)."""
    query = f"""
    WITH thread_statuses AS (
      SELECT
        thread_id,
        thread_status
      FROM `{PROJECT_ID}.{DATASET}.thread_state`
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
      INNER JOIN `{PROJECT_ID}.{DATASET}.interaction_event` ie
        ON ts.thread_id = ie.thread_id
      WHERE ie.thread_id IS NOT NULL
      GROUP BY ie.thread_id, ts.thread_status
    ),
    threads_with_messages AS (
      SELECT
        thread_id,
        thread_status,
        messages[OFFSET(0)].message_body AS last_message_body,
        CASE 
          WHEN ARRAY_LENGTH(messages) > 1 THEN messages[OFFSET(1)].message_body
          ELSE NULL
        END AS previous_message_body
      FROM recent_messages
    )
    SELECT
      twm.thread_id,
      twm.thread_status,
      twm.last_message_body,
      twm.previous_message_body
    FROM threads_with_messages twm
    LEFT JOIN `{PROJECT_ID}.{DATASET}.thread_state_explain` tse
      ON tse.thread_id = twm.thread_id
     AND tse.prompt_version = @prompt_version
    WHERE tse.thread_id IS NULL
    ORDER BY twm.thread_id
    LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("prompt_version", "STRING", PROMPT_VERSION),
            bigquery.ScalarQueryParameter("limit", "INT64", BATCH_LIMIT),
        ]
    )
    rows = bq.query(query, job_config=job_config).result()
    return [dict(r) for r in rows]


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from response, handling markdown code blocks and extra text."""
    text = text.strip()
    if not text:
        raise ValueError("Empty response from model")
    
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*?\}', text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    return json.loads(text)


def explain_thread_state(
    model: GenerativeModel,
    heuristic_status: str,
    last_message: str,
    prev_message: str = None
) -> Dict[str, Any]:
    """
    Explain thread state using LLM.
    
    Args:
        model: GenerativeModel instance
        heuristic_status: Current heuristic thread status (e.g., "open" or "closed")
        last_message: Body text of the last message
        prev_message: Body text of the previous message (optional)
    
    Returns:
        Dict with keys:
        - thread_status: "open" or "closed"
        - next_action_owner: "org", "customer", or "none"
        - status_reason: String (max 2 sentences)
        - confidence: Float between 0.0 and 1.0
    """
    prev_message_text = prev_message if prev_message else "N/A"
    
    prompt = f"""You are analyzing an email thread to determine its status and next action owner.

OUTPUT FORMAT (respond with ONLY this JSON, no preamble):
{{
  "thread_status": "open|closed",
  "next_action_owner": "org|customer|none",
  "status_reason": "Brief explanation in 1-2 sentences",
  "confidence": 0.0-1.0
}}

DECISION RULES:
1. thread_status:
   - "open" if awaiting response, unresolved issue, or pending action
   - "closed" if resolved, no further action needed, or explicit closure

2. next_action_owner:
   - "org" if customer is waiting for organization's response/action
   - "customer" if organization is waiting for customer's response/info
   - "none" if no action needed or thread is closed

3. Priority indicators:
   - Questions → open, action on responder
   - "Thanks/resolved/all set" → likely closed
   - Requests for info → open, action on recipient
   - Confirmations after resolution → closed
   - Follow-up promises ("I'll check and get back") → open, action on promiser

4. confidence:
   - 1.0: explicit closure/clear question
   - 0.7-0.9: strong indicators present
   - 0.4-0.6: ambiguous but reasonable inference
   - <0.4: very unclear, default to keeping open

INPUTS:
Heuristic status: {heuristic_status}
Previous message: {prev_message_text}
Last message: {last_message}

Respond with ONLY the JSON object, no markdown backticks, no explanation."""
    
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = model.generate_content(prompt)
            if not resp or not resp.text:
                raise ValueError("Empty response from model")
            
            raw = resp.text.strip()
            data = extract_json_from_response(raw)
            
            thread_status = data.get("thread_status", "").lower()
            next_action_owner = data.get("next_action_owner", "").lower()
            status_reason = data.get("status_reason", "")
            confidence = float(data.get("confidence", 0.0))
            
            # Validate thread_status
            if thread_status not in ("open", "closed"):
                raise ValueError(f"Invalid thread_status: {thread_status}. Must be 'open' or 'closed'.")
            
            # Validate next_action_owner
            if next_action_owner not in ("org", "customer", "none"):
                raise ValueError(f"Invalid next_action_owner: {next_action_owner}. Must be 'org', 'customer', or 'none'.")
            
            # Validate confidence
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Invalid confidence: {confidence}. Must be 0.0-1.0.")
            
            # Validate status_reason length (approximate - 2 sentences)
            if len(status_reason) > 500:
                status_reason = status_reason[:500].rsplit('.', 1)[0] + '.'
            
            return {
                "thread_status": thread_status,
                "next_action_owner": next_action_owner,
                "status_reason": status_reason,
                "confidence": confidence
            }
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                print(f"Attempt {attempt} failed: {e}. Retrying...")
                time.sleep(1.5 * attempt)
            else:
                print(f"Final error - Response was: {resp.text if 'resp' in locals() else 'No response'}")
    
    raise RuntimeError(f"Gemini call failed after retries: {last_err}")


<<<<<<< Updated upstream
=======
def fetch_threads_to_explain(bq: bigquery.Client, limit: int = BATCH_LIMIT) -> List[Dict[str, Any]]:
    """Fetch threads that need explanation from BigQuery."""
    query = f"""
    WITH thread_statuses AS (
      SELECT
        thread_id,
        thread_status
      FROM `{PROJECT_ID}.{DATASET}.thread_state`
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
      INNER JOIN `{PROJECT_ID}.{DATASET}.interaction_event` ie
        ON ts.thread_id = ie.thread_id
      WHERE ie.thread_id IS NOT NULL
      GROUP BY ie.thread_id, ts.thread_status
    ),
    threads_with_messages AS (
      SELECT
        thread_id,
        thread_status,
        messages[OFFSET(0)].message_body AS last_message_body,
        CASE 
          WHEN ARRAY_LENGTH(messages) > 1 THEN messages[OFFSET(1)].message_body
          ELSE NULL
        END AS previous_message_body
      FROM recent_messages
    )
    SELECT
      t.thread_id,
      t.thread_status,
      t.last_message_body,
      t.previous_message_body
    FROM threads_with_messages t
    LEFT JOIN `{PROJECT_ID}.{DATASET}.thread_state_explain` te
      ON t.thread_id = te.thread_id
     AND te.prompt_version = @prompt_version
    WHERE te.thread_id IS NULL
    ORDER BY t.thread_id
    LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("prompt_version", "STRING", PROMPT_VERSION),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )
    rows = bq.query(query, job_config=job_config).result()
    return [dict(r) for r in rows]


>>>>>>> Stashed changes
def ensure_thread_state_explain_table(bq: bigquery.Client) -> None:
    """Create the thread_state_explain table if it doesn't exist."""
    table_id = f"{PROJECT_ID}.{DATASET}.thread_state_explain"
    
    try:
        bq.get_table(table_id)
<<<<<<< Updated upstream
        print(f"Table {table_id} already exists.")
    except Exception:
        print(f"Creating table {table_id}...")
        schema = [
            bigquery.SchemaField("thread_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("thread_status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("next_action_owner", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("status_reason", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("confidence", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("prompt_version", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model_name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "STRING", mode="REQUIRED"),
        ]
        table_ref = bigquery.Table(table_id, schema=schema)
        table = bq.create_table(table_ref)
        print(f"Table {table_id} created successfully.")


def insert_explanations(bq: bigquery.Client, rows: List[Dict[str, Any]]) -> None:
    """Insert explanation results into BigQuery."""
    table_id = f"{PROJECT_ID}.{DATASET}.thread_state_explain"
    errors = bq.insert_rows_json(table_id, rows)  # streaming insert
=======
    except Exception:
        schema = [
            bigquery.SchemaField("thread_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("thread_status", "STRING"),
            bigquery.SchemaField("next_action_owner", "STRING"),
            bigquery.SchemaField("status_reason", "STRING"),
            bigquery.SchemaField("confidence", "FLOAT64"),
            bigquery.SchemaField("prompt_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        table_ref = bigquery.Table(table_id, schema=schema)
        bq.create_table(table_ref)


def insert_thread_state_explain(bq: bigquery.Client, rows: List[Dict[str, Any]]) -> None:
    """
    Insert thread state explanation results into BigQuery table thread_state_explain.
    
    Each row must include:
    - thread_id
    - thread_status
    - next_action_owner
    - status_reason
    - confidence
    - prompt_version
    - model_name
    - created_at (UTC timestamp as ISO string)
    """
    table_id = f"{PROJECT_ID}.{DATASET}.thread_state_explain"
    errors = bq.insert_rows_json(table_id, rows)
>>>>>>> Stashed changes
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")


<<<<<<< Updated upstream
def main():
    bq = bigquery.Client(project=PROJECT_ID)

    # Ensure table exists
    ensure_thread_state_explain_table(bq)

    # Init Vertex AI
    vertexai.init(project=PROJECT_ID, location=REGION)
    model = GenerativeModel(MODEL_NAME)

    to_explain = fetch_threads_to_explain(bq)
    if not to_explain:
        print("No new threads to explain.")
        return

    out_rows = []
    now_ts = datetime.now(timezone.utc).isoformat()

=======
def main(batch_limit: int = None):
    """
    Main function to process thread state explanations.
    
    Args:
        batch_limit: Number of threads to process (defaults to BATCH_LIMIT)
    """
    if batch_limit is None:
        batch_limit = BATCH_LIMIT
    
    bq = bigquery.Client(project=PROJECT_ID)
    
    ensure_thread_state_explain_table(bq)
    
    vertexai.init(project=PROJECT_ID, location=REGION)
    
    to_explain = fetch_threads_to_explain(bq, batch_limit)
    if not to_explain:
        return
    
    out_rows = []
    now_ts = datetime.now(timezone.utc)
    
>>>>>>> Stashed changes
    for i, item in enumerate(to_explain, start=1):
        thread_id = item["thread_id"]
        heuristic_status = item.get("thread_status") or "open"
        last_message = item.get("last_message_body") or ""
        prev_message = item.get("previous_message_body")
<<<<<<< Updated upstream

        # Avoid huge prompts: trim for thin slice
        last_message_trimmed = last_message[:8000]
        prev_message_trimmed = prev_message[:8000] if prev_message else None

        result = explain_thread_state(
            model=model,
=======
        
        last_message_trimmed = last_message[:8000] if last_message else ""
        prev_message_trimmed = prev_message[:8000] if prev_message else None
        
        result = explain_thread_state(
>>>>>>> Stashed changes
            heuristic_status=heuristic_status,
            last_message=last_message_trimmed,
            prev_message=prev_message_trimmed
        )
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
        out_rows.append({
            "thread_id": thread_id,
            "thread_status": result["thread_status"],
            "next_action_owner": result["next_action_owner"],
            "status_reason": result["status_reason"],
            "confidence": result["confidence"],
            "prompt_version": PROMPT_VERSION,
            "model_name": MODEL_NAME,
<<<<<<< Updated upstream
            "created_at": now_ts,
        })

        if i % 10 == 0:
            print(f"Explained {i}/{len(to_explain)} threads...")

    insert_explanations(bq, out_rows)
    print(f"Inserted {len(out_rows)} explanation rows into thread_state_explain.")


if __name__ == "__main__":
    main()
=======
            "created_at": now_ts.isoformat(),
        })
        
        if i % 10 == 0:
            print(f"Processed {i}/{len(to_explain)} threads...")
    
    if out_rows:
        insert_thread_state_explain(bq, out_rows)
        print(f"Inserted {len(out_rows)} explanation rows into thread_state_explain.")


if __name__ == "__main__":
    # Allow batch limit to be set via command line argument
    batch_limit = None
    if len(sys.argv) > 1:
        try:
            batch_limit = int(sys.argv[1])
        except ValueError:
            print(f"Invalid batch limit: {sys.argv[1]}. Using default: {BATCH_LIMIT}")
    
    main(batch_limit=batch_limit)
>>>>>>> Stashed changes

