from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Optimus API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    auto_create_tables: bool = False

    database_url: str = "postgresql+psycopg://optimus:optimus@localhost:5432/optimus"

    allowed_origins: str = "http://localhost:3000"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"

    auth_required: bool = True
    admin_username: str = "admin"
    admin_password: str = "change-me"
    jwt_secret_key: str = "change-this-jwt-secret-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60

    max_upload_size_bytes: int = 5_000_000
    rate_limit_max_requests: int = 180
    rate_limit_window_seconds: int = 60
    block_prompt_injection: bool = False

    audit_log_path: str = "logs/audit.jsonl"
    audit_export_max_lines: int = 5_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
