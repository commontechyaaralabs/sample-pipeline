@echo off
REM Startup script for FastAPI backend (Windows)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Set default to mock mode if not specified
if "%USE_MOCK_DATA%"=="" set USE_MOCK_DATA=true

echo Starting FastAPI server...
if "%USE_MOCK_DATA%"=="true" (
    echo Data source: MOCK
) else (
    echo Data source: BIGQUERY
)

REM Run uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

