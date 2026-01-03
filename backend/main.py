"""
FastAPI application entry point.

Enterprise-compliant setup:
- No credentials in code
- Uses Application Default Credentials for BigQuery
- Always uses BigQuery (no mock mode)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router

# Initialize FastAPI app
app = FastAPI(
    title="Thread Analytics API",
    description="Enterprise-compliant API for thread data analytics",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
# In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["threads"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "data_source": "bigquery",
        "message": "Thread Analytics API"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "data_source": "bigquery",
        "endpoints": {
            "threads": "/api/threads",
            "monthly_aggregates": "/api/threads/aggregates/monthly"
        }
    }

