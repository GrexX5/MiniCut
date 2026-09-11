"""PRD §3.1 — Détection automatique de la source depuis l'URL."""
import re

YOUTUBE_RE = re.compile(
    r"(youtube\.com/(watch|shorts|live|embed)|youtu\.be/)",
    re.IGNORECASE,
)
INSTAGRAM_RE = re.compile(r"instagram\.com/(reel|reels|p|tv)/", re.IGNORECASE)
TIKTOK_RE = re.compile(
    r"(tiktok\.com/|vm\.tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)",
    re.IGNORECASE,
)

SUPPORTED = ("youtube", "instagram", "tiktok")


def detect_source(url: str) -> str:
    """Retourne 'youtube' | 'instagram' | 'tiktok', lève ValueError sinon."""
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        raise ValueError("URL invalide : doit commencer par http(s)://")
    if YOUTUBE_RE.search(u):
        return "youtube"
    if INSTAGRAM_RE.search(u):
        return "instagram"
    if TIKTOK_RE.search(u):
        return "tiktok"
    raise ValueError(
        "Source non supportée en MVP : seuls YouTube, Instagram et TikTok sont acceptés."
    )
