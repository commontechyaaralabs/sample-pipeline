# Environment Variables Setup Guide

## 📁 File Locations

### Backend
- **Example file:** `backend/.env.example`
- **Your file:** `backend/.env` (create this by copying .env.example)
- **Location:** `E:\office\sample-pipeline\backend\.env`

### Frontend
- **Example file:** `frontend/.env.example`
- **Your file:** `frontend/.env.local` (create this by copying .env.example)
- **Location:** `E:\office\sample-pipeline\frontend\.env.local`

## 🚀 Quick Setup

### Backend Setup

1. **Navigate to backend folder:**
   ```powershell
   cd backend
   ```

2. **Copy the example file:**
   ```powershell
   copy .env.example .env
   ```

3. **Edit `.env` file with your values:**
   ```env
   USE_MOCK_DATA=true
   GCP_PROJECT_ID=clariversev1
   BIGQUERY_DATASET_ID=your-dataset
   FRONTEND_URL=http://localhost:3000
   ```

### Frontend Setup

1. **Navigate to frontend folder:**
   ```powershell
   cd frontend
   ```

2. **Copy the example file:**
   ```powershell
   copy .env.example .env.local
   ```

3. **Edit `.env.local` file (usually no changes needed for local dev):**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## 📋 Environment Variables Reference

### Backend Variables (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_MOCK_DATA` | No | `true` | `true` = mock data, `false` = BigQuery |
| `GCP_PROJECT_ID` | Yes (if BigQuery) | `your-project-id` | Your GCP project ID |
| `BIGQUERY_DATASET_ID` | Yes (if BigQuery) | `your-dataset` | BigQuery dataset name |
| `BIGQUERY_THREAD_LIST_VIEW` | No | `v_thread_list` | Thread list view name |
| `BIGQUERY_MONTHLY_AGGREGATES_VIEW` | No | `v_monthly_thread_aggregates` | Aggregates view name |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for CORS |

### Frontend Variables (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API URL |

## 🔧 Loading Environment Variables

### Backend (Python/FastAPI)

**Option 1: Manual loading (recommended for development)**
```python
# FastAPI automatically reads from environment
# Just set them before running uvicorn
```

**Option 2: Use python-dotenv (if you want .env file support)**
```python
# Add to requirements.txt: python-dotenv
# Then in main.py:
from dotenv import load_dotenv
load_dotenv()
```

**For now, set environment variables directly:**
```powershell
# Windows PowerShell
$env:USE_MOCK_DATA="true"
$env:GCP_PROJECT_ID="clariversev1"
uvicorn main:app --reload
```

### Frontend (Next.js)

Next.js automatically loads `.env.local` file. Just create it and restart the dev server.

**Important:** Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## 🎯 Common Scenarios

### Scenario 1: Local Development (Mock Data)
**Backend `.env`:**
```env
USE_MOCK_DATA=true
FRONTEND_URL=http://localhost:3000
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Scenario 2: Local Development (BigQuery)
**Backend `.env`:**
```env
USE_MOCK_DATA=false
GCP_PROJECT_ID=clariversev1
BIGQUERY_DATASET_ID=your-dataset
BIGQUERY_THREAD_LIST_VIEW=v_thread_list
BIGQUERY_MONTHLY_AGGREGATES_VIEW=v_monthly_thread_aggregates
FRONTEND_URL=http://localhost:3000
```

**Also authenticate:**
```powershell
gcloud auth application-default login
```

### Scenario 3: Production (Cloud Run)
**Set via Cloud Run deployment:**
```powershell
gcloud run deploy thread-analytics-api `
  --set-env-vars "USE_MOCK_DATA=false,GCP_PROJECT_ID=clariversev1,BIGQUERY_DATASET_ID=your-dataset,FRONTEND_URL=https://your-frontend.com"
```

## ⚠️ Security Notes

1. **`.env` and `.env.local` are gitignored** - they won't be committed
2. **Never commit credentials** - these files contain only configuration
3. **No secrets in env vars** - authentication uses ADC (Application Default Credentials)
4. **Production:** Set env vars via Cloud Run console or deployment command

## 🔍 Verify Your Setup

### Backend
```powershell
cd backend
python -c "import os; print('USE_MOCK_DATA:', os.getenv('USE_MOCK_DATA', 'not set'))"
```

### Frontend
```powershell
cd frontend
npm run dev
# Check browser console for API calls
```

## 📝 File Structure

```
sample-pipeline/
├── backend/
│   ├── .env              ← Create this (gitignored)
│   ├── .env.example      ← Template (committed)
│   └── ...
├── frontend/
│   ├── .env.local        ← Create this (gitignored)
│   ├── .env.example      ← Template (committed)
│   └── ...
└── ...
```

## 🆘 Troubleshooting

**Backend can't read env vars:**
- Make sure you're setting them before running uvicorn
- Or use python-dotenv to load from .env file

**Frontend can't connect to backend:**
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Restart Next.js dev server after changing env vars
- Check backend is running on the correct port

**BigQuery errors:**
- Verify `USE_MOCK_DATA=false`
- Check `GCP_PROJECT_ID` and `BIGQUERY_DATASET_ID` are correct
- Authenticate: `gcloud auth application-default login`

