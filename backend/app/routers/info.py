"""POST /api/info — PRD §3.2 : métadonnées instantanées (titre, miniature, durée)."""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings
from ..services.detector import detect_source
from ..services.downloader import get_metadata

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api", tags=["info"])


class InfoRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)


@router.post("/info")
@limiter.limit(lambda: get_settings().RATE_INFO_PER_MIN)
def fetch_info(payload: InfoRequest, request: Request):
    try:
        detect_source(payload.url)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    try:
        meta = get_metadata(payload.url)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    except Exception:
        return {"ok": False, "error": "Service vidéo temporairement indisponible, réessaie."}
    if meta.get("is_live"):
        return {"ok": False, "error": "Les lives ne sont pas supportés en MVP."}
    if meta["duration"] and meta["duration"] > get_settings().MAX_SOURCE_DURATION:
        return {"ok": False, "error": "Vidéo trop longue pour le MVP (> 2h)."}
    return {"ok": True, "data": meta}
