from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./knightwise.db"
    stockfish_path: str = "/usr/local/bin/stockfish"
    openai_api_key: str | None = None
    lichess_token: str | None = None
    frontend_origin: str = "http://localhost:3000"


settings = Settings()
