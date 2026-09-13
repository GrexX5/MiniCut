"""Accès DB + quotas journaliers (PRD §3.4).

Compatible SQLite (dev) et TiDB Serverless (prod, MySQL-dialect).
En V2, brancher Clerk : user_key = clerk user id, sinon fallback IP.
"""
from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from ..config import get_settings
from ..models import Base, QuotaUsage

_settings = get_settings()


def _connect_args_for(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    if url.startswith("mysql+pymysql"):
        # TiDB Serverless exige SSL. `ssl={"ssl": True}` validé le 2026-09-13
        # (pymysql attend un dict, pas un bool). Pas de `?ssl=...` dans l'URL.
        return {"ssl": {"ssl": True}}
    return {}


engine = create_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args_for(_settings.DATABASE_URL),
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def quota_limit_for(user_key: str, authenticated: bool = False) -> int:
    s = get_settings()
    if authenticated or not user_key.startswith("ip:"):
        return s.DAILY_QUOTA_FREE
    return s.DAILY_QUOTA_ANON


def check_and_consume_quota(user_key: str, authenticated: bool = False) -> tuple[bool, int, int]:
    """Incrémente le compteur du jour si sous quota.

    Retourne (ok, used, limit). `used` inclut la consommation courante si ok.
    """
    limit = quota_limit_for(user_key, authenticated)
    today = date.today().isoformat()
    with SessionLocal() as db:
        row = db.execute(
            select(QuotaUsage).where(QuotaUsage.user_key == user_key, QuotaUsage.day == today)
        ).scalar_one_or_none()
        if row is None:
            row = QuotaUsage(user_key=user_key, day=today, count=0)
            db.add(row)
            db.flush()
        if row.count >= limit:
            return False, row.count, limit
        row.count += 1
        db.commit()
        return True, row.count, limit


def quota_status(user_key: str, authenticated: bool = False) -> tuple[int, int]:
    limit = quota_limit_for(user_key, authenticated)
    today = date.today().isoformat()
    with SessionLocal() as db:
        row = db.execute(
            select(QuotaUsage).where(QuotaUsage.user_key == user_key, QuotaUsage.day == today)
        ).scalar_one_or_none()
        return (row.count if row else 0), limit
