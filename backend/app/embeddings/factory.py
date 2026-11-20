"""Build the configured embedder."""

from app.config import Settings
from app.embeddings.base import Embedder
from app.embeddings.cache import CachedEmbedder
from app.embeddings.hashing import HashingEmbedder
from app.embeddings.http import HTTPEmbedder


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "http":
        inner: Embedder = HTTPEmbedder(
            settings.embedding_base_url, settings.embedding_model,
            settings.embedding_dim, settings.embedding_api_key,
        )
    elif settings.embedding_provider == "hashing":
        inner = HashingEmbedder(dim=settings.embedding_dim)
    else:
        raise ValueError(f"unknown embedding provider '{settings.embedding_provider}'")
    return CachedEmbedder(inner)
