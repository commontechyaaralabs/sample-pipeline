# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Backend (FastAPI)

```bash
cd backend

# Windows
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Default: Mock Mode** (no GCP setup needed)

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Visit: `http://localhost:3000`

## 🔄 Switching to BigQuery Mode

### Local Development

1. Authenticate with GCP:
   ```bash
   gcloud auth application-default login
   ```

2. Set environment variable:
   ```bash
   # Windows
   set USE_MOCK_DATA=false
   
   # Linux/Mac
   export USE_MOCK_DATA=false
   ```

3. Set BigQuery config (optional, defaults provided):
   ```bash
   set GCP_PROJECT_ID=your-project-id
   set BIGQUERY_DATASET_ID=your-dataset
   ```

4. Restart FastAPI server

### Production (Cloud Run)

Deploy with:
```bash
gcloud run deploy thread-analytics-api \
  --source . \
  --service-account cloud-run-frontend-sa@PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars USE_MOCK_DATA=false,GCP_PROJECT_ID=PROJECT_ID
```

## ✅ Verify It Works

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test Threads Endpoint:**
   ```bash
   curl http://localhost:8000/api/threads?limit=5
   ```

3. **Test Aggregates Endpoint:**
   ```bash
   curl http://localhost:8000/api/threads/aggregates/monthly?months=3
   ```

4. **Frontend:**
   - Open `http://localhost:3000`
   - Should see threads and monthly aggregates

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.12+)
- Verify dependencies: `pip list | grep fastapi`

### Frontend can't connect to backend
- Check backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/main.py`
- Verify `NEXT_PUBLIC_API_URL` in frontend

### BigQuery errors
- Verify authentication: `gcloud auth application-default print-access-token`
- Check service account has BigQuery permissions
- Verify views exist: `v_thread_list`, `v_monthly_thread_aggregates`

## 📝 Environment Variables Reference

### Backend
- `USE_MOCK_DATA` - `true` (mock) or `false` (BigQuery)
- `GCP_PROJECT_ID` - Your GCP project ID
- `BIGQUERY_DATASET_ID` - BigQuery dataset name
- `BIGQUERY_THREAD_LIST_VIEW` - View name (default: `v_thread_list`)
- `BIGQUERY_MONTHLY_AGGREGATES_VIEW` - View name (default: `v_monthly_thread_aggregates`)
- `FRONTEND_URL` - Frontend domain for CORS

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

## 🔒 Security Reminder

✅ **DO:**
- Use Application Default Credentials
- Attach service accounts in Cloud Run
- Use Workload Identity in GKE

❌ **DON'T:**
- Commit service account keys
- Store credentials in environment variables
- Hardcode project IDs in production

