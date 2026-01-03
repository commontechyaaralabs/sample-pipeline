#!/bin/bash
# Startup script for FastAPI backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting FastAPI server..."
echo "Data source: BigQuery"
echo ""
echo "Note: Ensure you have authenticated with gcloud:"
echo "  gcloud auth application-default login"
echo ""

# Run uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

