from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./tp_bot.db"

    control_bot_token: str = ""
    intake_bot_token: str = ""
    control_group_id: int = 0
    owner_telegram_id: int = 0
    intake_bot_username: str = ""
    invite_expires_hours: int = 24
    mtg_rotation_targets: str = ""
    mtg_rotation_front_domain: str = "google.com"
    mtg_rotation_timeout_sec: int = 45
    mtg_rotation_ssh_key_path: str = ""


settings = Settings()
