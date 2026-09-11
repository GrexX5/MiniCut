"""Jobs asynchrones — PRD §3.3 + Rapport §1 (pas de Serverless timeout).

Flow :
  POST /api/jobs {url, start, end} -> {job_id} (queued, quota consommé)
  GET  /api/jobs/{id}              -> polling {status, progress, download_url}
  GET  /api/download/{id}          -> fichier .mp4 (TTL 10 min, PRD §5)
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..models import DownloadJob
from ..services import quotas
from ..services.detector import detect_source
from ..services.downloader import download_clip, get_metadata
from ..services.quotas import SessionLocal
from ..utils import cleanup
from ..utils.timeparse import parse_hms_to_seconds, validate_clip_range

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api", tags=["jobs"])

# Registre en mémoire (suffisant pour 1 instance Koyeb Eco en MVP).
# La DB garde l'historique ; le dict garde la progression temps réel.
JOBS: dict[str, dict] = {}


class JobRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)
    # PRD §3.2 : saisie précise HH:MM:SS OU secondes (le front envoie des secondes)
    start: str | int | float
    end: str | int | float


def _user_key(request: Request) -> tuple[str, bool]:
    """Clerk en V2 : header X-User-Id. MVP : IP (PRD §3.4 — 1 essai anonyme)."""
    uid = request.headers.get("x-user-id", "").strip()
    if uid:
        return f"user:{uid}", True
    ip = get_remote_address(request) or "unknown"
    return f"ip:{ip}", False


def _run_job(job_id: str, url: str, start: float, end: float) -> None:
    JOBS[job_id]["status"] = "processing"

    def _progress(p: float) -> None:
        JOBS[job_id]["progress"] = round(float(p), 3)

    try:
        path = download_clip(url, start, end, job_id=job_id, on_progress=_progress)
        size = path.stat().st_size if path.exists() else 0
        JOBS[job_id].update(
            {"status": "done", "progress": 1.0, "file": str(path), "size": size}
        )
        with SessionLocal() as db:
            row = db.get(DownloadJob, job_id)
            if row:
                row.status = "done"
                row.file_path = str(path)
                row.file_size = size
                db.commit()
        # PRD §5 : suppression après 10 min
        cleanup.schedule_deletion(path)
    except Exception as e:
        JOBS[job_id].update({"status": "error", "error": str(e)[:500]})
        # Anti storage-leak (Rapport §6) : purger les partiels du job en échec.
        # Le .mp4 final réussi est lui nettoyé via schedule_deletion (TTL 10 min).
        try:
            for leftover in get_settings().tmp_path.glob(f"{job_id}*"):
                if leftover.is_file():
                    leftover.unlink(missing_ok=True)
        except OSError:
            pass
        with SessionLocal() as db:
            row = db.get(DownloadJob, job_id)
            if row:
                row.status = "error"
                row.error = str(e)[:500]
                db.commit()


@router.post("/jobs")
@limiter.limit(lambda: get_settings().RATE_JOBS_PER_MIN)
def create_job(payload: JobRequest, request: Request, bg: BackgroundTasks):
    settings = get_settings()
    # 1. Source supportée ?
    try:
        source = detect_source(payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Temps valides ?
    try:
        start = parse_hms_to_seconds(payload.start)
        end = parse_hms_to_seconds(payload.end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Durée totale (pour valider le range + afficher l'erreur tôt)
    duration = 0.0
    try:
        meta = get_metadata(payload.url)
        duration = float(meta.get("duration") or 0)
    except Exception:
        pass  # on validera sans la durée totale
    try:
        validate_clip_range(start, end, duration or None, settings.MAX_CLIP_DURATION)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Quota (PRD §3.4)
    user_key, authenticated = _user_key(request)
    ok, used, limit = quotas.check_and_consume_quota(user_key, authenticated)
    if not ok:
        raise HTTPException(
            status_code=429,
            detail=f"Quota journalier atteint ({used}/{limit}). Crée un compte gratuit pour continuer.",
        )

    # 5. Créer le job + lancer en arrière-plan (long polling côté front)
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "url": payload.url,
        "source": source,
        "start": start,
        "end": end,
        "error": "",
    }
    with SessionLocal() as db:
        db.add(
            DownloadJob(
                id=job_id,
                url=payload.url,
                source=source,
                start=start,
                end=end,
                status="queued",
                user_key=user_key,
            )
        )
        db.commit()

    bg.add_task(_run_job, job_id, payload.url, start, end)
    return {"ok": True, "job_id": job_id, "quota": {"used": used, "limit": limit}}


@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        # Fallback DB (ex: restart instance)
        with SessionLocal() as db:
            row = db.get(DownloadJob, job_id)
            if not row:
                raise HTTPException(status_code=404, detail="Job inconnu")
            return {
                "ok": True,
                "job_id": job_id,
                "status": row.status,
                "progress": 0.0,
                "download_url": f"/api/download/{job_id}" if row.status == "done" else None,
                "error": row.error,
            }
    out = {
        "ok": True,
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "download_url": f"/api/download/{job_id}" if job["status"] == "done" else None,
        "error": job.get("error", ""),
    }
    return out


@router.get("/download/{job_id}")
def download_file(job_id: str):
    job = JOBS.get(job_id)
    path_str = (job or {}).get("file", "")
    if not path_str:
        with SessionLocal() as db:
            row = db.get(DownloadJob, job_id)
            if row and row.file_path:
                path_str = row.file_path
    if not path_str:
        raise HTTPException(status_code=404, detail="Fichier non prêt ou expiré (TTL 10 min).")
    path = Path(path_str)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Fichier expiré (nettoyé après 10 min). Retente un découpage.")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"minicut-{job_id}.mp4",
    )


@router.get("/quota")
def my_quota(request: Request):
    user_key, authenticated = _user_key(request)
    used, limit = quotas.quota_status(user_key, authenticated)
    return {"ok": True, "used": used, "limit": limit, "authenticated": authenticated}
