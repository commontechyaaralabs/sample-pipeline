@echo off
REM Startup script for FastAPI backend (Windows)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting FastAPI server...
echo Data source: BigQuery
echo.
echo Note: Ensure you have authenticated with gcloud:
echo   gcloud auth application-default login
echo.

REM Run uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

