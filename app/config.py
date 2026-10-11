from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    vllm_base_url: str = "http://localhost:8001/v1"
    vllm_api_key: str = "not-needed"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    embed_model: str = "BAAI/bge-m3"
    embed_dim: int = 1024

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # DB
    database_url: str = "postgresql+asyncpg://rei:rei@localhost:5432/rei"

    # Ingestion
    inbox_dir: str = "./data/inbox"
    processed_dir: str = "./data/processed"
    law_dir: str = "./data/law"
    tips_dir: str = "./data/tax_tips"
    ocr_enabled: bool = True
    pii_mask: bool = True

    # Retrieval
    rag_top_k: int = 12
    rag_rerank: bool = True
    rag_min_score: float = 0.35

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()