from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _root_env_file() -> str | None:
    """`3 project/.env` when running on host (three levels above backend/app/). In Docker `/app/app/config.py` has no fourth parent — use env from compose only."""
    try:
        root = Path(__file__).resolve().parents[3] / ".env"
    except IndexError:
        return None
    return str(root) if root.is_file() else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_root_env_file(), extra="ignore")

    database_url: str = "postgresql+psycopg2://saas:saas@localhost:25434/saas"
    redis_url: str = "redis://localhost:26481/0"
    jwt_secret: str = "dev-secret-change-me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    demo_mode: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    # OpenRouter / Azure OpenAI: set base URL (e.g. https://openrouter.ai/api/v1) and a model id (e.g. openai/gpt-4o-mini)
    openai_base_url: str | None = None
    openai_http_referer: str | None = None  # optional; OpenRouter recommends HTTP-Referer
    google_client_id: str | None = None
    google_client_secret: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    frontend_origin: str = "http://localhost:5175"
    oauth_redirect_uri: str = "http://localhost:28181/oauth/google/callback"  # override via env OAUTH_REDIRECT_URI


settings = Settings()
