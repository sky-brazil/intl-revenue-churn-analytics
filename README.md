# 03 - Revenue Dashboard and Churn Prediction (MVP API)

Practical analytics API focused on SaaS revenue visibility and proactive churn prevention.

## Delivered capabilities

- account ingestion endpoint for subscription snapshots
- revenue metrics (`MRR`, `ARR`, active/canceled accounts)
- cohort retention report by start month
- churn risk scoring with high-risk banding
- actionable high-risk alerts for customer success teams

## Business positioning

1. **Starter** - revenue metrics and basic executive reporting
2. **Growth** - churn scoring and account-level alerts
3. **Enterprise** - model governance, monitoring, and integration workflows

## Tech stack

- **Backend:** FastAPI
- **Storage:** SQLAlchemy + SQLite (PostgreSQL-ready with `DATABASE_URL`)
- **Scoring:** transparent heuristic risk model for explainability
- **Tests:** Pytest

## Project structure

```text
app/
  db.py
  main.py
  models.py
  schemas.py
  scoring.py
tests/
  test_api.py
```

## API highlights

- `POST /accounts/import` - bulk upsert account records
- `GET /accounts` - list account snapshots
- `GET /metrics/revenue` - total accounts, MRR, ARR, and averages
- `GET /metrics/cohorts` - retention by cohort month
- `GET /churn/predictions` - account-level churn score and risk band
- `GET /alerts/high-risk` - prioritized list for immediate outreach
- `POST /accounts/reset` - local reset endpoint for demos

## Local setup

```bash
cd projects/03-revenue-churn-analytics
pip3 install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

## Run tests

```bash
cd projects/03-revenue-churn-analytics
pytest -q
```

## Docker

```bash
cd projects/03-revenue-churn-analytics
docker compose up --build
```
