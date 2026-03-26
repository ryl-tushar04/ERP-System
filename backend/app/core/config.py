from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "ERP System API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = True

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "erp_system"
    postgres_pool_min_size: int = 1
    postgres_pool_max_size: int = 10

    llm_provider: str = Field(default="groq", env="LLM_PROVIDER")
    llm_model: str = Field(default="openai/gpt-oss-20b", env="LLM_MODEL")
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, env="OPENAI_BASE_URL")
    groq_api_key: str | None = Field(default=None, env="GROQ_API_KEY")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", env="GROQ_BASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        allow_population_by_field_name = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
