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

# Run uvicorn (exclude workers directory from reload watch)
uvicorn main:app --reload --reload-exclude "workers/*" --host 0.0.0.0 --port 8000

