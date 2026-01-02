#!/bin/bash
# Startup script for FastAPI backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set default to mock mode if not specified
export USE_MOCK_DATA=${USE_MOCK_DATA:-true}

echo "Starting FastAPI server..."
echo "Data source: $([ "$USE_MOCK_DATA" = "true" ] && echo "MOCK" || echo "BIGQUERY")"

# Run uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

