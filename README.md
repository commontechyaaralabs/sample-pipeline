# Thread Analytics Pipeline

Enterprise-compliant thread analytics application with FastAPI backend and Next.js frontend.

## Architecture

### Security Principles

✅ **No credentials in code**  
✅ **No service account keys**  
✅ **No environment variables for secrets**  
✅ **Application Default Credentials (ADC) only**  
✅ **Infrastructure-managed identity**

### Components

- **Backend**: FastAPI with mock/BigQuery data switching
- **Frontend**: Next.js with TypeScript
- **Data Layer**: Repository pattern with mock and BigQuery implementations
- **Authentication**: GCP Workload Identity / Application Default Credentials

## Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server (requires gcloud auth for BigQuery)
# For local development, authenticate first:
# gcloud auth application-default login

uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and will call the backend at `http://localhost:8000`.

## API Endpoints

### GET /api/threads
Retrieve a list of threads.

**Query Parameters:**
- `limit` (int, default: 10): Maximum number of threads to return (1-100)

**Response:**
```json
[
  {
    "thread_id": "t-001",
    "last_message_ts": "2025-01-15T10:30:00",
    "message_count": 5,
    "thread_status": "open",
    "sentiment": "neg",
    "confidence": 0.87,
    "prompt_version": "v0.1",
    "model_name": "gemini"
  }
]
```

### GET /api/threads/aggregates/monthly
Retrieve monthly thread aggregates.

**Query Parameters:**
- `months` (int, default: 6): Number of months to retrieve (1-24)

**Response:**
```json
[
  {
    "month": "2025-01",
    "thread_count": 120,
    "pos_threads": 65,
    "neutral_threads": 35,
    "neg_threads": 20
  }
]
```

## Deployment

### Cloud Run Deployment

1. **Get your GCP Project ID**:
   ```bash
   gcloud config get-value project
   ```
   Note the output (e.g., `my-project-123`). You'll use this in the next steps.

2. **Create Service Account** (one-time setup):
   ```bash
   # Replace PROJECT_ID with your actual project ID from step 1
   PROJECT_ID=$(gcloud config get-value project)  # Or set manually: PROJECT_ID="your-project-id"
   
   gcloud iam service-accounts create cloud-run-frontend-sa \
     --display-name="Cloud Run Frontend Service Account"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataViewer"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.jobUser"
   ```
   
   **Windows PowerShell users:** Replace `$PROJECT_ID` with your actual project ID:
   ```powershell
   $PROJECT_ID = "your-project-id"  # e.g., "clariversev1"
   
   gcloud iam service-accounts create cloud-run-frontend-sa `
     --display-name="Cloud Run Frontend Service Account"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID `
     --member="serviceAccount:cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com" `
     --role="roles/bigquery.dataViewer"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID `
     --member="serviceAccount:cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com" `
     --role="roles/bigquery.jobUser"
   ```

3. **Deploy using Cloud Build**:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml
   ```

4. **Or deploy manually**:
   ```bash
   # Replace PROJECT_ID with your actual project ID
   PROJECT_ID=$(gcloud config get-value project)
   
   gcloud run deploy thread-analytics-api \
     --source . \
     --region us-central1 \
     --service-account cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com \
     --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET_ID=flipkart_slices
   ```
   
   **Windows PowerShell:**
   ```powershell
   $PROJECT_ID = "your-project-id"
   
   gcloud run deploy thread-analytics-api `
     --source . `
     --region us-central1 `
     --service-account cloud-run-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com `
     --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET_ID=flipkart_slices"
   ```

### Environment Variables

**Backend (Cloud Run):**
- `GCP_PROJECT_ID`: Your GCP project ID (default: `clariversev1`)
- `BIGQUERY_DATASET_ID`: Your BigQuery dataset ID (default: `flipkart_slices`)
- `BIGQUERY_THREAD_STATE_TABLE`: Table name (default: `thread_state`)
- `BIGQUERY_MESSAGE_SENTIMENT_TABLE`: Table name (default: `message_sentiment`)
- `BIGQUERY_THREAD_LIST_VIEW`: View name (default: `v_thread_list`)
- `BIGQUERY_MONTHLY_AGGREGATES_VIEW`: View name (default: `v_monthly_thread_aggregates`)
- `BIGQUERY_USE_VIEWS`: Use views instead of direct table queries (default: `true`)
- `FRONTEND_URL`: Frontend domain for CORS

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## BigQuery Views Required

The backend expects these views to exist:

### v_thread_list
```sql
SELECT
  thread_id,
  last_message_ts,
  message_count,
  thread_status,
  sentiment,
  confidence,
  prompt_version,
  model_name
FROM your_table
ORDER BY last_message_ts DESC
```

### v_monthly_thread_aggregates
```sql
SELECT
  FORMAT_DATE('%Y-%m', DATE_TRUNC(month, MONTH)) as month,
  COUNT(*) as thread_count,
  COUNTIF(sentiment = 'pos') as pos_threads,
  COUNTIF(sentiment = 'neutral') as neutral_threads,
  COUNTIF(sentiment = 'neg') as neg_threads
FROM your_table
GROUP BY month
ORDER BY month DESC
```

## Development

### Local Development Setup
- Requires `gcloud auth application-default login` for BigQuery access
- Uses `bigquery_repo.py` for data (always uses BigQuery)
- Requires BigQuery tables and views to exist:
  - Tables (created by backend team): `thread_state`, `message_sentiment`
  - Views (we create): `v_thread_list`, `v_monthly_thread_aggregates`
- For local testing:
  1. Authenticate: `gcloud auth application-default login`
  2. Ensure you have access to the BigQuery dataset
  3. Run: `uvicorn main:app --reload --port 8000`

## Security Compliance

This architecture satisfies:
- ✅ SOC2 requirements
- ✅ ISO 27001 standards
- ✅ GCP Security Foundations
- ✅ No long-lived secrets
- ✅ Infrastructure-managed identity
- ✅ Least-privilege IAM

## Project Structure

```
backend/
├── api/
│   └── routes.py          # FastAPI routes
├── data/
│   ├── repository.py      # Interface definition
│   ├── mock_repo.py       # Mock implementation
│   └── bigquery_repo.py    # BigQuery implementation (ADC)
├── main.py                # FastAPI app
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image
└── cloudbuild.yaml       # Cloud Build config

frontend/
├── app/
│   ├── page.tsx          # Main dashboard page
│   └── layout.tsx        # Root layout
├── components/
│   ├── ThreadList.tsx    # Thread list component
│   └── MonthlyAggregates.tsx  # Aggregates component
├── lib/
│   └── api.ts            # API client
└── package.json          # Node dependencies
```

## License

Enterprise Internal Use Only

