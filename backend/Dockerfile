# Mini Cut Backend — image Koyeb-ready (Rapport §2 : Docker indispensable pour FFmpeg)
FROM python:3.11-slim

# FFmpeg binaire système (requis par yt-dlp --download-sections + découpe)
# + curl pour le HEALTHCHECK (sonde Koyeb / docker run local)
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
  CMD curl -f http://localhost:8000/health || exit 1

# 1 worker suffit sur instance Eco 512MB ; timeout large pour les longues vidéos
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "120"]
