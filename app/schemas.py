"""Pydantic schemas for analytics API."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountIn(BaseModel):
    external_id: str = Field(min_length=2, max_length=80)
    account_name: str = Field(min_length=2, max_length=200)
    mrr: float = Field(gt=0)
    billing_cycle: Literal["monthly", "yearly"] = "monthly"
    status: Literal["active", "past_due", "canceled"] = "active"
    started_at: date
    last_active_at: date
    support_tickets_30d: int = Field(ge=0)
    payment_failures_90d: int = Field(ge=0)
    nps_score: int = Field(ge=0, le=10)


class ImportAccountsIn(BaseModel):
    accounts: list[AccountIn]


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    account_name: str
    mrr: float
    billing_cycle: str
    status: str
    started_at: date
    last_active_at: date
    support_tickets_30d: int
    payment_failures_90d: int
    nps_score: int


class RevenueMetricsOut(BaseModel):
    total_accounts: int
    active_accounts: int
    canceled_accounts: int
    mrr: float
    arr: float
    avg_mrr_per_account: float


class ChurnPredictionOut(BaseModel):
    account_id: int
    external_id: str
    account_name: str
    churn_risk_score: float
    risk_band: Literal["low", "medium", "high"]


class CohortOut(BaseModel):
    cohort_month: str
    accounts_in_cohort: int
    active_accounts: int
    retention_rate: float
