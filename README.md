# Mini Cut — extraits YouTube / TikTok / Instagram sans filigrane

> Vision (PRD) : l'outil le plus rapide et le plus simple pour extraire des portions
> précises de vidéos YouTube et télécharger des contenus Instagram/TikTok sans
> filigrane, en moins de 3 clics. Voir `PRD_Mini_Cut.md` + `Rapport_Architecture_Mini_Cut.md`.

## État du MVP (Semaine 1–3 du Rapport §5)

| Étape | Statut | Dossier |
|---|---|---|
| PoC `yt-dlp` + `ffmpeg` (sections partielles, bypass filigrane) | ✅ script prêt | `backend/scripts/poc_cut.py` |
| API FastAPI async + nettoyage 10 min + rate-limit + quotas | ✅ scaffoldé | `backend/` |
| Front Next.js : input universel, métadonnées, double slider, polling, download | ✅ build OK | `frontend/` |
| Auth Clerk + TiDB quotas prod | 🔲 à brancher (quotas IP + `x-user-id` prêts) | `backend/app/services/quotas.py` |

## Architecture (Rapport §1–§2)

```
[Vercel : Next.js] --POST /api/info, /api/jobs--> [Koyeb : FastAPI + FFmpeg + yt-dlp]
        |<--poll GET /api/jobs/{id} + GET /api/download/{id}--|
                                                          +--> [TiDB Serverless]
```

Pas de Serverless timeout : jobs en `BackgroundTasks` + polling front toutes les 2s.
Téléchargement partiel `--download-sections "*start-end"` (Rapport §6 : jamais de full
download inutile). Fichiers purgés après 600s (PRD §5).

## Démarrage rapide

### 1. Backend (Python 3.11 + FFmpeg requis)

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                            # Linux/Mac : cp .env.example .env
uvicorn app.main:app --reload --port 8000
# PoC : python scripts/poc_cut.py "https://www.youtube.com/watch?v=..." --start 10 --end 25
```

### 2. Frontend (Node 20+, déjà vérifié : `npm run lint` + `npm run build` OK)

```bash
cd frontend
copy .env.example .env.local                      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                                       # http://localhost:3000
```

## Déploiement gratuit (Rapport §3)

- **Front** → Vercel : root `frontend/`, env `NEXT_PUBLIC_API_URL=https://<api>.koyeb.app`.
- **Back** → Koyeb : service Docker sur `backend/` (FFmpeg inclus), port 8000, health `/health`,
  env `ENV=prod`, `FRONTEND_ORIGINS=https://<front>.vercel.app`, `DATABASE_URL=<TiDB mysql+pymysql>`.
- **DB/Auth** → TiDB Serverless + Clerk (V2 : envoyer le user id dans le header `x-user-id`,
  déjà supporté par `GET /api/quota` et `POST /api/jobs`).

## Anti-pièges (Rapport §6)

- IP-ban YouTube : `YTDLP_COOKIES_FILE` / `PROXY_URL` en variables d'env, déjà câblés dans `downloader.py`.
- Storage-leak : `schedule_deletion()` + `purge_expired_tmp()` au boot, TTL 10 min.
- RAM Eco 512MB : `concurrent_fragment_downloads=4`, 1 worker uvicorn, clips ≤ 5 min (`MAX_CLIP_DURATION`).
