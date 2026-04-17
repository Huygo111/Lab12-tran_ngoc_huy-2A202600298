from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "My Production Agent"
    app_version: str = "1.0.0"
    environment: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"

    redis_url: str = "redis://localhost:6379/0"
    agent_api_key: str = "dev-secret-key"

    log_level: str = "INFO"
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    daily_budget_usd: float = 1.0

    class Config:
        env_file = ".env"


settings = Settings()
