"""PRD §5 — nettoyage automatique des .mp4 après 10 minutes (anti storage-leak, Rapport §6)."""
import asyncio
import time
from pathlib import Path

from ..config import get_settings


def schedule_deletion(path: str | Path, delay: int | None = None) -> None:
    """Planifie la suppression d'un fichier après `delay` secondes (défaut FILE_TTL_SECONDS)."""
    seconds = delay if delay is not None else get_settings().FILE_TTL_SECONDS
    target = Path(path)

    async def _delete_later() -> None:
        await asyncio.sleep(seconds)
        try:
            if target.exists():
                target.unlink()
        except OSError:
            pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_delete_later())
    except RuntimeError:
        # Pas de loop (contexte sync) : fallback thread bloquant détaché
        import threading

        def _sync() -> None:
            time.sleep(seconds)
            try:
                if target.exists():
                    target.unlink()
            except OSError:
                pass

        threading.Thread(target=_sync, daemon=True).start()


def purge_expired_tmp(max_age_seconds: int | None = None) -> int:
    """Supprime au démarrage les fichiers tmp plus vieux que FILE_TTL_SECONDS. Retourne le nb supprimé."""
    settings = get_settings()
    limit = max_age_seconds if max_age_seconds is not None else settings.FILE_TTL_SECONDS
    now = time.time()
    removed = 0
    tmp = settings.tmp_path
    for f in tmp.glob("*"):
        try:
            if f.is_file() and (now - f.stat().st_mtime) > limit:
                f.unlink()
                removed += 1
        except OSError:
            continue
    return removed
