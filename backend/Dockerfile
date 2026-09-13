# Mini Cut Backend — image Docker (FFmpeg inclus). Compatible Koyeb / Render / Fly.
# Render injecte $PORT (défaut 10000) ; Koyeb utilisait 8000 fixe.
FROM python:3.11-slim

# FFmpeg binaire système (requis par yt-dlp --download-sections + découpe)
# + curl pour le HEALTHCHECK (sonde /health)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.example ./.env.example

# Dossier temporaire des .mp4 (TTL 10 min, PRD §5)
RUN mkdir -p tmp

ENV ENV=prod
ENV TMP_DIR=/app/tmp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# 1 worker suffit sur instance 512MB ; timeout large pour les longues vidéos.
# Forme shell pour honorer $PORT de Render (fallback 8000 en local/Koyeb).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 120
