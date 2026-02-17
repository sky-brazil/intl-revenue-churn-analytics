"""FastAPI service for revenue intelligence and churn alerts."""

from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import CustomerAccount
from .schemas import (
    AccountOut,
    ChurnPredictionOut,
    CohortOut,
    ImportAccountsIn,
    RevenueMetricsOut,
)
from .scoring import churn_risk_score, risk_band

ACTIVE_STATUSES = {"active", "past_due"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Revenue and Churn Analytics API",
    description="SaaS metrics, retention cohorts, churn predictions, and risk alerts.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/accounts/import")
def import_accounts(payload: ImportAccountsIn, db: Session = Depends(get_db)) -> dict[str, int]:
    inserted = 0
    updated = 0

    for account_data in payload.accounts:
        account = db.scalar(
            select(CustomerAccount).where(CustomerAccount.external_id == account_data.external_id)
        )
        if account:
            account.account_name = account_data.account_name
            account.mrr = account_data.mrr
            account.billing_cycle = account_data.billing_cycle
            account.status = account_data.status
            account.started_at = account_data.started_at
            account.last_active_at = account_data.last_active_at
            account.support_tickets_30d = account_data.support_tickets_30d
            account.payment_failures_90d = account_data.payment_failures_90d
            account.nps_score = account_data.nps_score
            updated += 1
        else:
            db.add(
                CustomerAccount(
                    external_id=account_data.external_id,
                    account_name=account_data.account_name,
                    mrr=account_data.mrr,
                    billing_cycle=account_data.billing_cycle,
                    status=account_data.status,
                    started_at=account_data.started_at,
                    last_active_at=account_data.last_active_at,
                    support_tickets_30d=account_data.support_tickets_30d,
                    payment_failures_90d=account_data.payment_failures_90d,
                    nps_score=account_data.nps_score,
                )
            )
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "total": len(payload.accounts)}


@app.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db)) -> list[CustomerAccount]:
    return list(db.scalars(select(CustomerAccount).order_by(CustomerAccount.id)).all())


@app.get("/metrics/revenue", response_model=RevenueMetricsOut)
def revenue_metrics(db: Session = Depends(get_db)) -> RevenueMetricsOut:
    accounts = list(db.scalars(select(CustomerAccount)).all())

    total_accounts = len(accounts)
    active_accounts = len([account for account in accounts if account.status in ACTIVE_STATUSES])
    canceled_accounts = len([account for account in accounts if account.status == "canceled"])

    mrr = round(sum(account.mrr for account in accounts if account.status in ACTIVE_STATUSES), 2)
    arr = round(mrr * 12, 2)
    avg_mrr = round((mrr / active_accounts), 2) if active_accounts else 0.0

    return RevenueMetricsOut(
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        canceled_accounts=canceled_accounts,
        mrr=mrr,
        arr=arr,
        avg_mrr_per_account=avg_mrr,
    )


@app.get("/metrics/cohorts", response_model=list[CohortOut])
def cohort_retention(db: Session = Depends(get_db)) -> list[CohortOut]:
    accounts = list(db.scalars(select(CustomerAccount)).all())
    cohorts: dict[str, list[CustomerAccount]] = defaultdict(list)

    for account in accounts:
        cohort_key = account.started_at.strftime("%Y-%m")
        cohorts[cohort_key].append(account)

    report: list[CohortOut] = []
    for cohort_key, cohort_accounts in sorted(cohorts.items()):
        total = len(cohort_accounts)
        active = len([account for account in cohort_accounts if account.status in ACTIVE_STATUSES])
        retention_rate = round((active / total), 3) if total else 0.0
        report.append(
            CohortOut(
                cohort_month=cohort_key,
                accounts_in_cohort=total,
                active_accounts=active,
                retention_rate=retention_rate,
            )
        )
    return report


@app.get("/churn/predictions", response_model=list[ChurnPredictionOut])
def churn_predictions(db: Session = Depends(get_db)) -> list[ChurnPredictionOut]:
    accounts = list(db.scalars(select(CustomerAccount)).all())
    predictions: list[ChurnPredictionOut] = []
    for account in accounts:
        score = churn_risk_score(account)
        predictions.append(
            ChurnPredictionOut(
                account_id=account.id,
                external_id=account.external_id,
                account_name=account.account_name,
                churn_risk_score=score,
                risk_band=risk_band(score),
            )
        )
    predictions.sort(key=lambda row: row.churn_risk_score, reverse=True)
    return predictions


@app.get("/alerts/high-risk")
def high_risk_alerts(db: Session = Depends(get_db)) -> dict[str, list[dict]]:
    accounts = list(db.scalars(select(CustomerAccount)).all())
    high_risk: list[dict] = []

    for account in accounts:
        score = churn_risk_score(account)
        band = risk_band(score)
        if band != "high" or account.status == "canceled":
            continue
        high_risk.append(
            {
                "account_id": account.id,
                "external_id": account.external_id,
                "account_name": account.account_name,
                "mrr": account.mrr,
                "score": score,
                "recommended_action": "Schedule CSM outreach and review billing health within 24h.",
            }
        )

    high_risk.sort(key=lambda item: item["score"], reverse=True)
    return {"alerts": high_risk}


@app.post("/accounts/reset")
def reset_accounts(db: Session = Depends(get_db)) -> dict[str, int]:
    deleted = db.query(CustomerAccount).delete()
    db.commit()
    return {"deleted": int(deleted)}
