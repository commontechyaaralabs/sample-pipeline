# Architecture Documentation

## Overview

Enterprise-compliant thread analytics pipeline with **zero credentials in code**. All authentication is handled by GCP infrastructure using Application Default Credentials (ADC).

## Design Principles

### 1. Identity Model (The Only Approved Model)

**Principle:** Code never handles credentials. Infrastructure handles identity.

- ✅ FastAPI authenticates to BigQuery using **Attached Service Account**
- ✅ Uses **Application Default Credentials (ADC)**
- ❌ No environment variables for secrets
- ❌ No JSON key files
- ❌ No secrets in code

### 2. Data Access Layer

```
backend/data/
├── repository.py      # Interface contract
├── mock_repo.py       # Mock implementation (local dev)
└── bigquery_repo.py   # BigQuery implementation (production)
```

**Switching Logic:**
- `USE_MOCK_DATA=true` → Uses `mock_repo.py` (default)
- `USE_MOCK_DATA=false` → Uses `bigquery_repo.py` (production)

**Why This is Policy-Compliant:**
- No credentials involved
- Only toggles logic, not secrets
- Safe to commit to version control

### 3. Authentication Flow

#### Local Development
```bash
gcloud auth application-default login
```
Uses user credentials from gcloud CLI.

#### Cloud Run
```bash
gcloud run deploy ... --service-account cloud-run-frontend-sa@...
```
Service account attached to Cloud Run instance.

#### GKE
Uses Workload Identity - pod gets GCP identity automatically.

#### GCE
Uses VM service account.

**Your code does not change** - ADC handles everything.

## Component Architecture

### Backend (FastAPI)

```
backend/
├── main.py              # FastAPI app entry point
├── api/
│   └── routes.py       # API endpoints
├── data/
│   ├── repository.py   # Interface
│   ├── mock_repo.py   # Mock data
│   └── bigquery_repo.py # BigQuery (ADC)
└── requirements.txt
```

**API Endpoints:**
- `GET /api/threads?limit=10`
- `GET /api/threads/aggregates/monthly?months=6`
- `GET /health` - Health check

### Frontend (Next.js)

```
frontend/
├── app/
│   ├── page.tsx        # Dashboard
│   └── layout.tsx      # Root layout
├── components/
│   ├── ThreadList.tsx
│   └── MonthlyAggregates.tsx
└── lib/
    └── api.ts          # API client
```

**Frontend never talks to BigQuery directly** - all data access goes through FastAPI.

## Data Flow

```
┌─────────────┐
│   Next.js   │
│  Frontend   │
└──────┬──────┘
       │ HTTP
       │ GET /api/threads
       ▼
┌─────────────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
       │
       ├─ USE_MOCK_DATA=true → mock_repo.py
       │
       └─ USE_MOCK_DATA=false → bigquery_repo.py
                                  │
                                  │ Application Default Credentials
                                  ▼
                           ┌──────────────┐
                           │   BigQuery   │
                           │    Views     │
                           └──────────────┘
```

## BigQuery Views Contract

Backend expects these views (provided by backend team):

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

## Security Compliance

### ✅ SOC2 Compliance
- No long-lived secrets
- Identity managed by infrastructure
- Audit trail via Cloud Logging

### ✅ ISO 27001 Compliance
- Least-privilege IAM
- No credential distribution
- Infrastructure-managed access

### ✅ GCP Security Foundations
- Service account attached to resources
- Workload Identity for GKE
- Application Default Credentials

### ✅ Internal Platform Team Requirements
- No keys in code
- No keys in environment variables
- No keys in version control
- Infrastructure handles identity

## Deployment Architecture

### Cloud Run (Recommended)

```
┌─────────────────────────────────┐
│      Cloud Run Service          │
│  ┌───────────────────────────┐  │
│  │   FastAPI Container       │  │
│  │   (thread-analytics-api)  │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  Service Account:               │
│  cloud-run-frontend-sa          │
└──────────────┬──────────────────┘
               │
               │ ADC (automatic)
               ▼
        ┌──────────────┐
        │   BigQuery   │
        │    Views     │
        └──────────────┘
```

**IAM Roles Required:**
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

### GKE (Alternative)

```
┌─────────────────────────────────┐
│         GKE Pod                 │
│  ┌───────────────────────────┐  │
│  │   FastAPI Container       │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  Workload Identity:             │
│  (automatic GCP identity)       │
└──────────────┬──────────────────┘
               │
               │ ADC (automatic)
               ▼
        ┌──────────────┐
        │   BigQuery   │
        │    Views     │
        └──────────────┘
```

## Environment Variables

### Backend (Non-Secret Configuration)

| Variable | Purpose | Example |
|----------|---------|---------|
| `USE_MOCK_DATA` | Toggle mock/BigQuery | `true` or `false` |
| `GCP_PROJECT_ID` | GCP project ID | `my-project-123` |
| `BIGQUERY_DATASET_ID` | Dataset name | `analytics` |
| `BIGQUERY_THREAD_LIST_VIEW` | View name | `v_thread_list` |
| `BIGQUERY_MONTHLY_AGGREGATES_VIEW` | View name | `v_monthly_thread_aggregates` |
| `FRONTEND_URL` | CORS origin | `https://app.example.com` |

**⚠️ These are NOT secrets** - they're configuration values.

### Frontend

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## What Frontend Lead Can Do Today

✅ **Build UI** - Fully functional with mock data  
✅ **Define API contracts** - Endpoints locked  
✅ **Create FastAPI structure** - Ready for deployment  
✅ **GCP-ready data layer** - Just flip the switch  

**Authentication is deferred to runtime infrastructure** - no action needed from frontend team.

## What Backend Lead Must Provide

1. **BigQuery Views:**
   - `v_thread_list`
   - `v_monthly_thread_aggregates`

2. **Service Account Setup:**
   - Create `cloud-run-frontend-sa`
   - Grant BigQuery permissions
   - Attach to Cloud Run

3. **Environment Configuration:**
   - Set `USE_MOCK_DATA=false` in production
   - Configure project/dataset IDs

## Testing Strategy

### Local Development
- Use mock mode (`USE_MOCK_DATA=true`)
- No GCP setup required
- Frontend fully functional

### Integration Testing
- Use BigQuery mode with test dataset
- Authenticate with `gcloud auth application-default login`
- Test against real views

### Production
- Deploy to Cloud Run with service account
- `USE_MOCK_DATA=false`
- Infrastructure handles authentication

## Monitoring & Observability

- **Cloud Logging:** Automatic for Cloud Run
- **Health Endpoint:** `GET /health`
- **Error Handling:** Structured error responses

## Future Enhancements

- [ ] Add authentication/authorization layer
- [ ] Add rate limiting
- [ ] Add caching layer
- [ ] Add metrics/telemetry
- [ ] Add request tracing

