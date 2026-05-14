from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o"
    database_url: str = "sqlite:///./stock_analyzer.db"
    analysis_score_threshold: int = 40
    price_cache_ttl_minutes: int = 15

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
