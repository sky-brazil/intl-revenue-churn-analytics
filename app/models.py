"""SQLAlchemy models for subscription analytics."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CustomerAccount(Base):
    __tablename__ = "customer_accounts"
    __table_args__ = (UniqueConstraint("external_id", name="uq_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    mrr: Mapped[float] = mapped_column(Float, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    last_active_at: Mapped[date] = mapped_column(Date, nullable=False)
    support_tickets_30d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_failures_90d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nps_score: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
