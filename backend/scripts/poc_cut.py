"""PoC Semaine 1 (Rapport §5.1) : valider yt-dlp + FFmpeg en local.

Usage :
    python scripts/poc_cut.py "https://www.youtube.com/watch?v=..." --start 10 --end 25
    python scripts/poc_cut.py "https://www.tiktok.com/..." --full
    python scripts/poc_cut.py "https://www.instagram.com/reel/..." --full

Vérifie : métadonnées, téléchargement partiel (sections), bypass filigrane natif.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.detector import detect_source
from app.services.downloader import download_clip, get_metadata
from app.utils.timeparse import format_seconds_to_hms


def main() -> int:
    ap = argparse.ArgumentParser(description="Mini Cut PoC — download + cut")
    ap.add_argument("url", help="URL YouTube / Instagram / TikTok")
    ap.add_argument("--start", default="0", help="Début HH:MM:SS ou secondes (défaut 0)")
    ap.add_argument("--end", default="15", help="Fin HH:MM:SS ou secondes (défaut 15)")
    ap.add_argument("--full", action="store_true", help="Télécharger la vidéo complète (pas de cut)")
    args = ap.parse_args()

    print(f"[1/4] Source : {detect_source(args.url)}")
    meta = get_metadata(args.url)
    print(f"[2/4] Titre : {meta['title']}")
    print(f"      Durée : {meta['duration_hms']} | Miniature : {meta['thumbnail'][:80]}")

    if args.full:
        from app.services.downloader import _base_ydl_opts
        import yt_dlp

        with yt_dlp.YoutubeDL(_base_ydl_opts({"outtmpl": "tmp/poc_full.%(ext)s", "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b", "merge_output_format": "mp4"})) as ydl:
            ydl.download([args.url])
        print("[3/4] Full download OK -> tmp/poc_full.* (vérifie l'absence de filigrane)")
        return 0

    from app.utils.timeparse import parse_hms_to_seconds

    start = parse_hms_to_seconds(args.start)
    end = parse_hms_to_seconds(args.end)
    print(f"[3/4] Clip : {format_seconds_to_hms(start)} -> {format_seconds_to_hms(end)} (sections partielles)")
    out = download_clip(args.url, start, end, job_id="poc")
    print(f"[4/4] OK -> {out} ({out.stat().st_size / 1e6:.1f} Mo)")
    print("Note : le fichier tmp/ est nettoyé après 10 min côté API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
