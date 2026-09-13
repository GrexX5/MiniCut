# TODO — Mini Cut (MVP pas à pas)

> Source : `PRD_Mini_Cut.md` + `Rapport_Architecture_Mini_Cut.md`.
> Ce fichier est mis à jour par l'assistant au fur et à mesure.
> Légende : `[x]` fait · `[>]` en cours · `[ ]` à faire.

## Étape 0 — Cadrage & scaffolding ✅
- [x] Lire PRD + rapport d'architecture
- [x] Scaffolder `backend/` (FastAPI, yt-dlp, FFmpeg, jobs async, quotas, cleanup 10 min, Dockerfile, PoC)
- [x] Scaffolder `frontend/` (Next.js, input universel, métadonnées, double slider, polling, download)
- [x] `npm run lint` + `npm run build` OK
- [x] Corriger imports relatifs backend (`..config`, `..models`, `..utils`)
- [x] Rédiger `README.md` + `.gitignore`

## Étape 1 — Environnement local ✅
- [x] Vérifier Node/npm (OK : Node v26, npm 11)
- [x] Installer Python 3.11 via winget (OK : Python 3.11.9)
- [x] Installer FFmpeg via winget (OK : ffmpeg 9.0.1 full_build)
- [ ] Docker — reporté à l'Étape 6 (inutile en local, requis seulement pour build/push Koyeb)
- Validation : `python --version` → 3.11.9, `ffmpeg -version` → 9.0.1. ✅

## Étape 2 — PoC vidéo (Rapport §5.1) [>]
- [x] Créer venv + `pip install -r requirements.txt` + `.env` (OK : venv Python 3.11, 30 paquets, yt-dlp 2026.8.19)
- [x] Lancer `scripts/poc_cut.py` sur 1 URL YouTube (`--start 10 --end 25`)
  → OK : Big Buck Bunny 4K, métadonnées + sections partielles (~20 Mo pour 15s, pas le film entier),
  `tmp/poc.mp4` = 15.000s h264/aac valide (vérifié ffprobe). TikTok/Instagram : en attente d'URLs de test.
- [ ] Tester 1 URL TikTok (`--full`, vérifier absence de filigrane)
- [ ] Tester 1 URL Instagram (`--full`, vérifier absence de filigrane)
- Validation : 3 fichiers MP4 lisibles dans `backend/tmp/`, extrait YouTube ≈ 15s.

## Étape 3 — API backend (Rapport §5.2) ✅
- [x] `uvicorn app.main:app` démarre, `GET /health` → `{"ok": true}` (OK : minicut-api dev)
- [x] `POST /api/info` YouTube → titre/miniature/durée OK ; URL invalide → `{"ok": false}` propre
- [x] `POST /api/jobs` 10s→25s → `done`, `GET /api/download/{id}` → MP4 20.7 Mo `video/mp4`
- [x] Cas d'erreur : extrait > 5 min → 400 ; quota anonyme `used=1/limit=1` consommé
- Validation : `scripts/test_api_e2e.py` → **8 OK / 0 KO** (TestClient, 2026-09-10).

## Étape 4 — Frontend local ✅ (auto) / 🔲 (manuel navigateur)
- [x] `.env.local` (`NEXT_PUBLIC_API_URL=http://localhost:8000`)
- [x] Backend (job) + `npm run dev` (job) : `/health` OK, page `/` 16 Ko avec "Mini Cut" + "Analyser"
- [ ] Parcours manuel navigateur (2 terminaux : `uvicorn … --port 8000` puis `npm run dev`) :
  coller URL YouTube → Analyser → slider → Couper & Télécharger → MP4
- Validation auto OK ; E2E cliquable à faire par l'utilisateur (sandbox sans navigateur).

## Étape 5 — Quotas, rate-limit, nettoyage (PRD §3.4/§5) ✅
- [x] Quota anonyme épuisé → 429 via API (sans download)
- [x] Logique quotas : anonyme 1/jour, `x-user-id` → 10/jour
- [x] Rafale `/api/info` : 10×200 puis 429 (SlowAPI OK)
- [x] `schedule_deletion` + `purge_expired_tmp` vérifiés
- Bugs trouvés et corrigés : purge des partiels en cas de job en échec (`jobs.py`) ;
  tests rendus idempotents (clés horodatées, pré-saturation quota).
- Validation : `scripts/test_quotas_e2e.py` → **5 OK / 0 KO**.

## Étape 6 — Docker (Koyeb-ready) ✅ (build délégué à Koyeb)
- [x] Revue Dockerfile : base 3.11-slim, FFmpeg, 1 worker, `TMP_DIR=/app/tmp`, `.env` via vars Koyeb
- [x] Ajout `.dockerignore` (contexte minimal) + `HEALTHCHECK /health` (curl)
- [x] Décision : pas de Docker Desktop local → Koyeb buildera depuis git (conforme Rapport §2)
- Validation : au déploiement Étape 7 (build Koyeb + `/health` 200).

## Étape 7 — Déploiement & sécurisation (Rapport §2/§3) [>]
- [x] Pré-requis git : repo initialisé + push `https://github.com/GrexX5/MiniCut` branche `main` (50 fichiers, `.env`/`*.db`/`node_modules` exclus) ✅ 2026-09-13
- [x] TiDB Serverless : `DATABASE_URL` MySQL, tables créées (`download_jobs`, `quota_usage` via `init_db()`) ✅ 2026-09-13 — URL simplifiée `mysql+pymysql://.../minicut` (SSL auto dans `quotas.py`), DB `minicut` créée
- [ ] Render (remplace Koyeb HS/Mistral 2026) : Blueprint `render.yaml`, Docker `backend/`, `/health`, vars prod (`ENV`, `TMP_DIR`, `DATABASE_URL` TiDB sans `?ssl=`)
- [ ] Vercel : projet `frontend/`, `NEXT_PUBLIC_API_URL` → Koyeb
- [ ] Clerk : login + envoi `x-user-id`, quota gratuit OK
- [ ] Anti IP-ban : `YTDLP_COOKIES_FILE` / `PROXY_URL` si blocage YouTube
- Validation : parcours complet en production sur les 3 sources.

## Journal
- 2026-09-10 : scaffolding MVP terminé, build front OK, imports backend corrigés.
- 2026-09-10 : `TODO.md` créé, démarrage Étape 1.
- 2026-09-10 (Étape 1) : Node v26.8.1 + npm 11.19.0 OK. Python, FFmpeg et Docker ABSENTS — installation requise avant Étape 2.
- 2026-09-10 (Étape 1) : Python 3.11.9 + FFmpeg 9.0.1 installés via winget et vérifiés. Docker reporté à l'Étape 6.
- 2026-09-10 (Étape 2) : PoC YouTube validé (Big Buck Bunny : 15.000s h264/aac, 20.7 Mo via sections partielles).
- 2026-09-10 (Étape 3) : E2E API 8/8 OK (health, info, job, download MP4, quota). Serveur fond tué par le shell → tests via TestClient.
- 2026-09-11 (Étape 4 auto) : backend + `npm run dev` en jobs, page `/` 16 Ko ("Mini Cut", "Analyser"). E2E navigateur à faire manuellement.
- 2026-09-11 (Étape 5) : 5/5 OK (quota 429, rate-limit 10+429, TTL). Fix purge partiels en échec + tests idempotents.
- 2026-09-11 (Étape 6) : Dockerfile revu + `.dockerignore` + HEALTHCHECK. Build local abandonné → Koyeb depuis git.
- 2026-09-13 (Étape 7, push GitHub OK) : `gh` installé, `auth login` GrexX5, branche `master`→`main`, `gh repo create MiniCut --public --push` → `https://github.com/GrexX5/MiniCut`. Prochaine : TiDB→Koyeb→Vercel→Clerk. Reste Étape 2 : URLs TikTok/Instagram pour PoC filigrane.
