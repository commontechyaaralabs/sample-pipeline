import json
import re
import time
from typing import Dict, Any

# Vertex AI (Gemini)
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "clariversev1"
REGION = "us-central1"

PROMPT_VERSION = "explain_v0.1"
MODEL_NAME = "gemini-2.0-flash"

MAX_RETRIES = 3

# Lazy initialization
_model = None


def _get_model() -> GenerativeModel:
    """Get or initialize the Gemini model."""
    global _model
    if _model is None:
        vertexai.init(project=PROJECT_ID, location=REGION)
        _model = GenerativeModel(MODEL_NAME)
    return _model


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
    heuristic_status: str,
    last_message: str,
    prev_message: str = None
) -> Dict[str, Any]:
    """
    Explain thread state using LLM.
    
    Args:
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
    model = _get_model()
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
                time.sleep(1.5 * attempt)
            else:
                pass
    
    raise RuntimeError(f"Gemini call failed after retries: {last_err}")


if __name__ == "__main__":
    # Simple test
    result = explain_thread_state(
        heuristic_status="open",
        last_message="When will my order be delivered?",
        prev_message="I placed an order yesterday."
    )
    print(json.dumps(result, indent=2))

