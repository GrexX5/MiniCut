"""Mini Cut — configuration centrale (PRD §5 + Rapport §2/§5)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Mini Cut API"
    ENV: str = "dev"  # dev | prod

    # CORS : URL du front Vercel + localhost pour le dev
    FRONTEND_ORIGINS: str = "http://localhost:3000"

    # DB : SQLite en local, TiDB Serverless en prod.
    # Ex TiDB : mysql+pymysql://user:password@gateway01.eu-central-1.prod.aws.tidbcloud.com:4000/minicut
    # (SSL auto ajouté par quotas.py, pas de `?ssl=` dans l'URL).
    DATABASE_URL: str = "sqlite:///./minicut.db"

    # Stockage temporaire des .mp4
    TMP_DIR: str = "./tmp"
    # PRD §5 : nettoyage automatique après 10 minutes
    FILE_TTL_SECONDS: int = 600

    # Garde-fous anti-abus (Rapport §6)
    MAX_CLIP_DURATION: int = 300  # 5 min max par extrait en MVP
    MAX_SOURCE_DURATION: int = 7200  # refuse les lives / vidéos > 2h en MVP
    DAILY_QUOTA_ANON: int = 1  # PRD §3.4 : 0 ou 1 essai gratuit sans compte
    DAILY_QUOTA_FREE: int = 10  # utilisateurs inscrits

    # Contournement IP-ban YouTube (Rapport §6) : optionnels
    YTDLP_COOKIES_FILE: str = ""  # ex: /app/cookies.txt (monté comme secret Koyeb)
    PROXY_URL: str = ""  # ex: http://user:pass@proxy:8080 (rotation IPv6 à moyen terme)

    # Rate limiting (PRD §5)
    RATE_INFO_PER_MIN: str = "10/minute"
    RATE_JOBS_PER_MIN: str = "5/minute"

    @property
    def tmp_path(self) -> Path:
        p = Path(self.TMP_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def frontend_origins_list(self) -> list[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
