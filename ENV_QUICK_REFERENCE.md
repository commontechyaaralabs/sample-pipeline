# Environment Variables Quick Reference

## 📍 File Locations

### Backend
- **Template:** `backend/.env.example` 
- **Your file:** `backend/.env` (create by copying .env.example)
- **Full path:** `E:\office\sample-pipeline\backend\.env`

### Frontend  
- **Template:** `frontend/.env.example`
- **Your file:** `frontend/.env.local` (create by copying .env.example)
- **Full path:** `E:\office\sample-pipeline\frontend\.env.local`

## 🚀 Quick Setup Commands

### Backend
```powershell
cd E:\office\sample-pipeline\backend
copy .env.example .env
# Then edit .env with your values
```

### Frontend
```powershell
cd E:\office\sample-pipeline\frontend
copy .env.example .env.local
# Usually no changes needed for local dev
```

## 📋 Required Environment Variables

### Backend (`backend/.env`)

```env
# Required for local development (mock mode)
USE_MOCK_DATA=true

# Required for BigQuery mode (production)
GCP_PROJECT_ID=clariversev1
BIGQUERY_DATASET_ID=your-dataset

# Optional (have defaults)
BIGQUERY_THREAD_LIST_VIEW=v_thread_list
BIGQUERY_MONTHLY_AGGREGATES_VIEW=v_monthly_thread_aggregates
FRONTEND_URL=http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## ✅ Your Current Setup

Based on your project, use these values:

**Backend `.env`:**
```env
USE_MOCK_DATA=true
GCP_PROJECT_ID=clariversev1
BIGQUERY_DATASET_ID=your-dataset
BIGQUERY_THREAD_LIST_VIEW=v_thread_list
BIGQUERY_MONTHLY_AGGREGATES_VIEW=v_monthly_thread_aggregates
FRONTEND_URL=http://localhost:3000
```

**Frontend `.env.local`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔧 How to Use

### Backend (Python)
Python doesn't automatically load `.env` files. You have two options:

**Option 1: Set environment variables manually (recommended)**
```powershell
$env:USE_MOCK_DATA="true"
$env:GCP_PROJECT_ID="clariversev1"
uvicorn main:app --reload
```

**Option 2: Use python-dotenv**
```powershell
# Add to requirements.txt: python-dotenv
pip install python-dotenv
# Then in main.py add: from dotenv import load_dotenv; load_dotenv()
```

### Frontend (Next.js)
Next.js automatically loads `.env.local` - just create it and restart:
```powershell
npm run dev
```

## ⚠️ Important Notes

1. **`.env` and `.env.local` are gitignored** - safe to create
2. **No secrets in these files** - only configuration
3. **Authentication uses ADC** - no credentials needed
4. **Restart servers** after changing env vars

## 📖 Full Documentation

See `ENV_SETUP.md` for detailed setup instructions.

