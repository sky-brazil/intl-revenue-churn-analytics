from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import db
from app.main import app


def make_client(tmp_path) -> TestClient:
    database_url = f"sqlite:///{tmp_path}/test.db"
    db.reset_engine(database_url)
    db.init_db()
    return TestClient(app)


def sample_payload() -> dict:
    today = date.today()
    return {
        "accounts": [
            {
                "external_id": "acc_001",
                "account_name": "Northwind",
                "mrr": 1000,
                "billing_cycle": "monthly",
                "status": "active",
                "started_at": str(today - timedelta(days=220)),
                "last_active_at": str(today - timedelta(days=5)),
                "support_tickets_30d": 1,
                "payment_failures_90d": 0,
                "nps_score": 9,
            },
            {
                "external_id": "acc_002",
                "account_name": "Contoso",
                "mrr": 2000,
                "billing_cycle": "monthly",
                "status": "past_due",
                "started_at": str(today - timedelta(days=140)),
                "last_active_at": str(today - timedelta(days=80)),
                "support_tickets_30d": 11,
                "payment_failures_90d": 2,
                "nps_score": 2,
            },
            {
                "external_id": "acc_003",
                "account_name": "Tailspin",
                "mrr": 1500,
                "billing_cycle": "yearly",
                "status": "canceled",
                "started_at": str(today - timedelta(days=320)),
                "last_active_at": str(today - timedelta(days=200)),
                "support_tickets_30d": 0,
                "payment_failures_90d": 0,
                "nps_score": 7,
            },
        ]
    }


def test_import_accounts_and_revenue_metrics(tmp_path) -> None:
    with make_client(tmp_path) as client:
        imported = client.post("/accounts/import", json=sample_payload())
        assert imported.status_code == 200, imported.text
        assert imported.json()["inserted"] == 3

        metrics = client.get("/metrics/revenue")
        assert metrics.status_code == 200, metrics.text
        payload = metrics.json()
        assert payload["total_accounts"] == 3
        assert payload["active_accounts"] == 2
        assert payload["canceled_accounts"] == 1
        assert payload["mrr"] == 3000
        assert payload["arr"] == 36000


def test_cohorts_predictions_and_high_risk_alerts(tmp_path) -> None:
    with make_client(tmp_path) as client:
        client.post("/accounts/import", json=sample_payload())

        cohorts = client.get("/metrics/cohorts")
        assert cohorts.status_code == 200, cohorts.text
        assert len(cohorts.json()) >= 2

        predictions = client.get("/churn/predictions")
        assert predictions.status_code == 200, predictions.text
        ordered = predictions.json()
        assert ordered[0]["external_id"] in {"acc_002", "acc_003"}

        alerts = client.get("/alerts/high-risk")
        assert alerts.status_code == 200, alerts.text
        alert_items = alerts.json()["alerts"]
        assert len(alert_items) >= 1
        assert any(item["external_id"] == "acc_002" for item in alert_items)


def test_reset_accounts(tmp_path) -> None:
    with make_client(tmp_path) as client:
        client.post("/accounts/import", json=sample_payload())
        reset = client.post("/accounts/reset")
        assert reset.status_code == 200, reset.text
        assert reset.json()["deleted"] == 3

        metrics = client.get("/metrics/revenue")
        assert metrics.status_code == 200
        assert metrics.json()["total_accounts"] == 0
