"""Cœur vidéo : métadonnées + téléchargement partiel + découpe FFmpeg.

Stratégie anti-gaspillage (Rapport §6 — "téléchargement complet inutile") :
1. On tente `yt-dlp --download-sections "*start-end"` => seul le segment est
   téléchargé puis découpé par FFmpeg côté yt-dlp. Idéal pour un extrait de
   15s dans une vidéo de 2h (PRD §2 Rapidité).
2. Fallback : téléchargement complet + `ffmpeg -ss -to` si la source/stream
   ne supporte pas les sections (certains CDN Instagram/TikTok).

Bypass filigrane (PRD §3.1) : yt-dlp récupère la source pure (pas de
filigrane TikTok/Instagram) tant qu'on ne passe pas par un enregistrement
d'écran — aucun post-traitement requis.
"""
from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from ..config import get_settings
from .detector import detect_source
from ..utils.timeparse import format_seconds_to_hms


def _base_ydl_opts(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    s = get_settings()
    # 720p max en MVP : divise RAM/CPU/disque par 2-4 vs 4K (crucial sur 512MB).
    ydl_format = (
        "bv*[height<=720][ext=mp4]+ba[ext=m4a]"
        "/b[height<=720][ext=mp4]"
        "/bv*[ext=mp4]+ba/b"
    )
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        # Instance gratuite 512MB (Render/Railway) : 2 fragments max en parallèle
        # (4 OOM le container au démarrage du download, constaté 2026-09-14).
        "concurrent_fragment_downloads": 2,
        # MVP : 720p max => 2-4x moins de RAM/CPU/disque qu'en 4K, suffisant
        # pour des extraits courts. Fallback sans limite si aucun flux ≤720p.
        "format": ydl_format,
        # Anti bot-check YouTube sur IP datacenter (Render) : client tv d'abord
        # (endpoint TVHTML5, historiquement le moins filtré), puis web
        # (formats complets, OK avec cookies) et android en dernier recours.
        # Cookies via YTDLP_COOKIES_FILE (déjà câblé ci-dessous).
        "extractor_args": {"youtube": {"player_client": ["tv", "web", "android"]}},
    }
    if s.YTDLP_COOKIES_FILE:
        opts["cookiefile"] = s.YTDLP_COOKIES_FILE
    if s.PROXY_URL:
        opts["proxy"] = s.PROXY_URL
    if extra:
        opts.update(extra)
    return opts


def get_metadata(url: str) -> dict[str, Any]:
    """PRD §3.2 — titre, miniature, durée. Lève ValueError avec message clair."""
    source = detect_source(url)  # valide le domaine d'abord
    try:
        with yt_dlp.YoutubeDL(_base_ydl_opts({"skip_download": True})) as ydl:
            info = ydl.extract_info(url, download=False)
    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
        # Sœurs (pas mère-fille) dans yt-dlp récent : attraper les deux.
        # Couvre les erreurs extracteur non wrappées (ex: challenge TikTok
        # sur IP datacenter, constaté 2026-09-14 en prod).
        raise ValueError(f"Impossible de lire cette vidéo ({source}) : {e}") from e
    if info is None:
        raise ValueError("Vidéo introuvable ou privée.")
    # Playlist déguisée : prendre la première entrée
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise ValueError("Playlist vide ou non supportée en MVP (une seule vidéo à la fois).")
        info = entries[0]

    duration = info.get("duration") or 0
    return {
        "source": source,
        "title": info.get("title") or "Sans titre",
        "thumbnail": info.get("thumbnail") or "",
        "duration": float(duration),
        "duration_hms": format_seconds_to_hms(float(duration)),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "webpage_url": info.get("webpage_url") or url,
        "is_live": bool(info.get("is_live")),
    }


def _check_ffmpeg() -> str:
    bin_path = shutil.which("ffmpeg")
    if not bin_path:
        raise RuntimeError("FFmpeg introuvable sur le serveur (apt install ffmpeg / image Docker).")
    return bin_path


def cut_with_ffmpeg(input_path: Path, output_path: Path, start: float, end: float) -> None:
    """Découpe précise avec ré-encodage léger (compatible tous players)."""
    _check_ffmpeg()
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start),
        "-to",
        str(end),
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        "-y",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("FFmpeg timeout (vidéo trop lourde pour l'instance Eco).") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Échec FFmpeg : {(e.stderr or '')[-500:]}") from e


def _section_str(start: float, end: float) -> str:
    # Format exigé par yt-dlp --download-sections : "*HH:MM:SS-HH:MM:SS"
    return f"*{format_seconds_to_hms(start)}-{format_seconds_to_hms(end)}"


def download_clip(
    url: str,
    start: float,
    end: float,
    job_id: str | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> Path:
    """Télécharge UNIQUEMENT le segment [start, end] et retourne le .mp4 final.

    - Youtube : sections natives => rapide, peu de RAM (instance Koyeb Eco 512MB).
    - Instagram/TikTok (courtes vidéos) : sections ou fallback full + cut.
    """
    settings = get_settings()
    detect_source(url)
    job_id = job_id or uuid.uuid4().hex[:12]
    tmp = settings.tmp_path
    out_final = tmp / f"{job_id}.mp4"

    def _hook(d: dict[str, Any]) -> None:
        if on_progress is None:
            return
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                if total:
                    on_progress(min(0.9, done / total * 0.9))
            elif d.get("status") == "finished":
                on_progress(0.9)
        except Exception:
            pass

    # --- Tentative 1 : téléchargement partiel (économe) ---
    partial_template = str(tmp / f"{job_id}_partial.%(ext)s")
    try:
        opts = _base_ydl_opts(
            {
                "outtmpl": partial_template,
                "merge_output_format": "mp4",
                "download_ranges": yt_dlp.utils.download_range_func(None, [(start, end)]),
                "download_sections": [_section_str(start, end)],
                "force_keyframes_at_cuts": True,
                "progress_hooks": [_hook],
            }
        )
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        # yt-dlp + ffmpeg produisent déjà le segment => renommer en final
        candidates = sorted(tmp.glob(f"{job_id}_partial.*"))
        videos = [c for c in candidates if c.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")]
        if videos:
            best = videos[0]
            if best.suffix.lower() != ".mp4" or True:
                # Normaliser en mp4 faststart via un remux rapide (sans ré-encodage si possible)
                try:
                    _check_ffmpeg()
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-i",
                            str(best),
                            "-c",
                            "copy",
                            "-movflags",
                            "+faststart",
                            "-y",
                            str(out_final),
                        ],
                        check=True,
                        capture_output=True,
                        timeout=300,
                    )
                    best.unlink(missing_ok=True)
                except Exception:
                    # Dernier recours : garder le fichier tel quel
                    if not out_final.exists():
                        best.rename(out_final)
            if out_final.exists() and out_final.stat().st_size > 0:
                if on_progress:
                    on_progress(1.0)
                return out_final
    except Exception:
        # On bascule sur le fallback ci-dessous (full + cut)
        pass

    # --- Tentative 2 (fallback) : full download puis cut FFmpeg ---
    full_template = str(tmp / f"{job_id}_full.%(ext)s")
    opts = _base_ydl_opts(
        {
            "outtmpl": full_template,
            "merge_output_format": "mp4",
            "progress_hooks": [_hook],
        }
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
        raise RuntimeError(f"Téléchargement impossible (IP-ban ? cookies ?). Détail : {e}") from e

    candidates = sorted(tmp.glob(f"{job_id}_full.*"))
    videos = [c for c in candidates if c.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov", ".m4a")]
    if not videos:
        raise RuntimeError("Téléchargement vide : format non supporté.")
    src = videos[0]
    try:
        cut_with_ffmpeg(src, out_final, start, end)
    finally:
        try:
            src.unlink(missing_ok=True)
        except OSError:
            pass
    if on_progress:
        on_progress(1.0)
    return out_final
