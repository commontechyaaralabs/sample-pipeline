import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

from google.cloud import bigquery

# Vertex AI (Gemini)
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "clariversev1"
DATASET = "flipkart_slices"
REGION = "us-central1"

PROMPT_VERSION = "sentiment_v0.2"  # Updated to 1-5 scale
MODEL_NAME = "gemini-2.0-flash"  # Updated to valid model name

BATCH_LIMIT = 300  # number of threads/messages to score per run
MAX_RETRIES = 3


def fetch_latest_messages_to_score(bq: bigquery.Client) -> List[Dict[str, Any]]:
    query = f"""
    WITH latest_msg AS (
      SELECT
        thread_id,
        ARRAY_AGG(STRUCT(message_id, body_text, event_ts) ORDER BY event_ts DESC LIMIT 1)[OFFSET(0)] AS lm
      FROM `{PROJECT_ID}.{DATASET}.interaction_event`
      GROUP BY thread_id
    )
    SELECT
      latest_msg.thread_id AS thread_id,
      lm.message_id AS message_id,
      lm.body_text AS body_text
    FROM latest_msg
    LEFT JOIN `{PROJECT_ID}.{DATASET}.message_sentiment` ms
      ON ms.thread_id = latest_msg.thread_id
     AND ms.message_id = latest_msg.lm.message_id
     AND ms.prompt_version = @prompt_version
    WHERE ms.message_id IS NULL
    ORDER BY lm.event_ts DESC
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


def call_gemini_sentiment(model: GenerativeModel, text: str) -> Tuple[int, float]:
    """
    Returns (sentiment_score, confidence_float).
    Sentiment scale: 1-5
    1 – Happy: The customer expresses satisfaction, appreciation, or a clearly positive experience.
    2 – Bit Irritated: The customer shows mild annoyance or impatience without strong emotional distress.
    3 – Moderately Concerned: The customer expresses concern or worry that has not escalated into frustration or anger.
    4 – Anger: The customer shows clear frustration or anger, often using strong or confrontational language.
    5 – Frustrated: The customer is extremely upset, indicating repeated issues, delays, or severe dissatisfaction.
    Confidence: 0.0 - 1.0
    """
    prompt = f"""
You are a strict sentiment classifier.

Task:
Given the email text, return JSON with:
- sentiment: an integer between 1 and 5
- confidence: number between 0 and 1

Sentiment Scale:
1 – Happy: The customer expresses satisfaction, appreciation, or a clearly positive experience.
2 – Bit Irritated: The customer shows mild annoyance or impatience without strong emotional distress.
3 – Moderately Concerned: The customer expresses concern or worry that has not escalated into frustration or anger.
4 – Anger: The customer shows clear frustration or anger, often using strong or confrontational language.
5 – Frustrated: The customer is extremely upset, indicating repeated issues, delays, or severe dissatisfaction.

Rules:
- Choose the sentiment score (1-5) that best matches the customer's emotional state.
- Use 3 if the sentiment is truly mixed or unclear.
- Confidence reflects your certainty in the classification (0.0 to 1.0).
- Output MUST be valid JSON only. No extra text.

Email text:
{text}
"""
    # Simple retry logic
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = model.generate_content(prompt)
            if not resp or not resp.text:
                raise ValueError("Empty response from model")
            
            raw = resp.text.strip()
            data = extract_json_from_response(raw)
            
            sentiment = int(data.get("sentiment", 0))
            confidence = float(data.get("confidence", 0.0))
            
            if sentiment not in (1, 2, 3, 4, 5):
                raise ValueError(f"Invalid sentiment: {sentiment}. Must be 1-5.")
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Invalid confidence: {confidence}. Must be 0.0-1.0.")
            return sentiment, confidence
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                print(f"Attempt {attempt} failed: {e}. Retrying...")
                time.sleep(1.5 * attempt)
            else:
                print(f"Final error - Response was: {resp.text if 'resp' in locals() else 'No response'}")
    raise RuntimeError(f"Gemini call failed after retries: {last_err}")


def ensure_message_sentiment_table(bq: bigquery.Client) -> None:
    """Create the message_sentiment table if it doesn't exist."""
    table_id = f"{PROJECT_ID}.{DATASET}.message_sentiment"
    
    try:
        bq.get_table(table_id)
        print(f"Table {table_id} already exists.")
    except Exception:
        print(f"Creating table {table_id}...")
        schema = [
            bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("thread_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("sentiment", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("confidence", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("prompt_version", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "STRING", mode="REQUIRED"),
        ]
        table_ref = bigquery.Table(table_id, schema=schema)
        table = bq.create_table(table_ref)
        print(f"Table {table_id} created successfully.")


def insert_sentiments(bq: bigquery.Client, rows: List[Dict[str, Any]]) -> None:
    table_id = f"{PROJECT_ID}.{DATASET}.message_sentiment"
    errors = bq.insert_rows_json(table_id, rows)  # streaming insert
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")


def main():
    bq = bigquery.Client(project=PROJECT_ID)

    # Ensure table exists
    ensure_message_sentiment_table(bq)

    # Init Vertex AI
    vertexai.init(project=PROJECT_ID, location=REGION)
    model = GenerativeModel(MODEL_NAME)

    to_score = fetch_latest_messages_to_score(bq)
    if not to_score:
        print("No new latest messages to score.")
        return

    out_rows = []
    now_ts = datetime.now(timezone.utc).isoformat()

    for i, item in enumerate(to_score, start=1):
        thread_id = item["thread_id"]
        message_id = item["message_id"]
        body_text = item.get("body_text") or ""

        sentiment, confidence = call_gemini_sentiment(model, body_text)

        out_rows.append({
            "message_id": message_id,
            "thread_id": thread_id,
            "sentiment": sentiment,
            "confidence": confidence,
            "prompt_version": PROMPT_VERSION,
            "model_name": MODEL_NAME,
            "created_at": now_ts,
        })

        if i % 20 == 0:
            print(f"Scored {i}/{len(to_score)} messages...")

    insert_sentiments(bq, out_rows)
    print(f"Inserted {len(out_rows)} sentiment rows into message_sentiment.")


if __name__ == "__main__":
    main()
