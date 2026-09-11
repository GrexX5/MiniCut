"""Modèles SQLAlchemy — compatibles SQLite (local) et TiDB/MySQL (prod).

PRD §3.4 / §5 + Rapport §2 : profils + quotas + historique.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid4
    url: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="")
    start: Mapped[float] = mapped_column(Float, default=0)
    end: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0)
    file_path: Mapped[str] = mapped_column(Text, default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    user_key: Mapped[str] = mapped_column(String(128), default="anon")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class QuotaUsage(Base):
    """Compteur journalier par user_key (IP ou user id Clerk) + date YYYY-MM-DD."""

    __tablename__ = "quota_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_key: Mapped[str] = mapped_column(String(128), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
