"""Mini Cut API — point d'entrée FastAPI (Rapport §2 : FastAPI + yt-dlp + FFmpeg)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .routers import info, jobs
from .services.quotas import init_db
from .utils.cleanup import purge_expired_tmp

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Les jobs sont suivis en mémoire : après un crash/restart (fréquent sur
    # instance gratuite 512MB), les lignes restées "queued"/"processing" en DB
    # ne finiront jamais => les marquer en erreur avec un message relançable.
    try:
        from sqlalchemy import update

        from .models import DownloadJob
        from .services.quotas import SessionLocal

        with SessionLocal() as db:
            db.execute(
                update(DownloadJob)
                .where(DownloadJob.status.in_(["queued", "processing"]))
                .values(status="error", error="Redémarrage serveur pendant le traitement, relance ta découpe.")
            )
            db.commit()
    except Exception:
        pass
    purge_expired_tmp()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins_list + ["*"] if settings.ENV == "dev" else settings.frontend_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(info.router)
    app.include_router(jobs.router)

    @app.get("/health")
    def health():
        return {"ok": True, "service": "minicut-api", "env": settings.ENV}

    return app


app = create_app()
