from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PideFácil Integration API"
    debug: bool = False

    database_url: str
    cliente_a_database_url: str
    cliente_b_database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
