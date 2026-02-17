"""Churn scoring and revenue metric helpers."""

from __future__ import annotations

from datetime import date

from .models import CustomerAccount


def churn_risk_score(account: CustomerAccount, today: date | None = None) -> float:
    if account.status == "canceled":
        return 100.0

    today = today or date.today()
    days_inactive = max(0, (today - account.last_active_at).days)

    inactivity = min(1.0, days_inactive / 60) * 0.40
    tickets = min(1.0, account.support_tickets_30d / 12) * 0.20
    payment_failures = min(1.0, account.payment_failures_90d / 3) * 0.25
    nps_penalty = min(1.0, max(0, 6 - account.nps_score) / 6) * 0.15

    return round((inactivity + tickets + payment_failures + nps_penalty) * 100, 2)


def risk_band(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
