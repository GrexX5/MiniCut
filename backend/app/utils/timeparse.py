"""PRD §3.2 — parsing temporel HH:MM:SS <-> secondes."""
import re

_HMS_RE = re.compile(r"^(?:(\d+):)?([0-5]?\d):([0-5]\d)$|^(?:(\d+):)?([0-5]?\d)$|^(\d+)$")


def parse_hms_to_seconds(value: str | int | float) -> float:
    """Accepte 'SS', 'MM:SS', 'HH:MM:SS' ou nombre. Retourne secondes (float)."""
    if isinstance(value, (int, float)):
        v = float(value)
        if v < 0:
            raise ValueError("Le temps doit être >= 0")
        return v
    s = str(value or "").strip()
    if not s:
        raise ValueError("Temps vide")
    # Nombre brut ?
    try:
        v = float(s)
        if v < 0:
            raise ValueError("Le temps doit être >= 0")
        return v
    except ValueError:
        pass
    parts = s.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        raise ValueError(f"Format temporel invalide : '{value}' (attendu HH:MM:SS)")
    if len(nums) == 2:  # MM:SS
        m, sec = nums
        return m * 60 + sec
    if len(nums) == 3:  # HH:MM:SS
        h, m, sec = nums
        return h * 3600 + m * 60 + sec
    raise ValueError(f"Format temporel invalide : '{value}' (attendu HH:MM:SS)")


def format_seconds_to_hms(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def validate_clip_range(start: float, end: float, duration: float | None, max_clip: int) -> None:
    if start < 0 or end <= 0:
        raise ValueError("Start/End doivent être positifs")
    if end <= start:
        raise ValueError("La fin doit être après le début")
    if (end - start) > max_clip:
        raise ValueError(f"Extrait trop long : max {max_clip}s en MVP")
    if duration and duration > 0:
        if start >= duration:
            raise ValueError("Le début dépasse la durée totale de la vidéo")
        if end > duration:
            raise ValueError("La fin dépasse la durée totale de la vidéo")
