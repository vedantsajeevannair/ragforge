"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAGFORGE_", env_file=".env", extra="ignore")

    app_name: str = "RAGForge"
    data_dir: Path = BACKEND_DIR / "data"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5
    contextual_headers: bool = False
    # Weight of the dense ranking in hybrid fusion (BM25 is 1.0). Unset means 0.5 for the
    # offline hashing embedder, which is weaker than BM25, and 1.0 for real embedding models.
    dense_weight: float | None = None

    @property
    def effective_dense_weight(self) -> float:
        if self.dense_weight is not None:
            return self.dense_weight
        return 0.5 if self.embedding_provider == "hashing" else 1.0
    embedding_provider: str = "hashing"
    embedding_dim: int = 512
    embedding_model: str = ""
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    llm_provider: str = "extractive"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    jwt_secret: str = ""
    jwt_expiry_minutes: int = 60 * 12
    max_upload_mb: int = 20
    # Uploads larger than this are indexed in the background and return 202 + a job id.
    async_upload_kb: int = 2048
    ask_rate_per_minute: int = 30
    log_level: str = "INFO"
    json_logs: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("data_dir")
    @classmethod
    def _anchor_relative_data_dir(cls, value: Path) -> Path:
        # A relative path would land wherever the server happens to be started.
        return value if value.is_absolute() else (BACKEND_DIR / value).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
