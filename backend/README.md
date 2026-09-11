# Mini Cut — Backend (FastAPI + yt-dlp + FFmpeg)

## Lancer en local

Prérequis : Python 3.11+, FFmpeg installé.

```bash
cd backend
python -m venv .venv
# Windows : .venv\Scripts\activate | Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

PoC Semaine 1 (Rapport §5.1) :

```bash
python scripts/poc_cut.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --start 10 --end 25
```

## Endpoints MVP

| Méthode | Route | Usage (PRD) |
|---|---|---|
| `GET` | `/health` | sonde Koyeb |
| `POST` | `/api/info` `{url}` | §3.2 métadonnées (titre, miniature, durée) |
| `POST` | `/api/jobs` `{url, start, end}` | §3.3 job asynchrone (quota consommé) |
| `GET` | `/api/jobs/{id}` | polling front (queued/processing/done/error) |
| `GET` | `/api/download/{id}` | fichier `.mp4` final (TTL 10 min) |
| `GET` | `/api/quota` | compteur journalier |

`start`/`end` acceptent secondes ou `HH:MM:SS`.

## Déploiement Koyeb (Rapport §2)

1. Push ce dossier (Dockerfile à la racine du service).
2. Koyeb → New Service → GitHub → `backend/` → Builder `Dockerfile`.
3. Port `8000`, health check `/health`.
4. Variables d'env : `ENV=prod`, `FRONTEND_ORIGINS=https://<ton-app>.vercel.app`, `DATABASE_URL=<TiDB>`.
5. Secret optionnel anti IP-ban : monter `cookies.txt` et définir `YTDLP_COOKIES_FILE=/app/cookies.txt`.
