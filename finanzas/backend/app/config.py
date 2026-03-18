from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://finanzas:finanzas@localhost:5432/finanzas"
    app_name: str = "Finanzas Personales"
    debug: bool = False


settings = Settings()
