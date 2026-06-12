from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Meridian Risk API
    meridian_api_url: str = "http://127.0.0.1:8000"
    meridian_timeout: int = 10

    # Output
    output_dir: str = "output"

    # Target maturity level (1-5) used when no target profile exists
    default_target_maturity: int = 3


settings = Settings()
