"""Dense retriever: embed the query, search the vector store."""

from app.embeddings.base import Embedder
from app.retrieval.base import Retriever
from app.vectorstore.base import MetadataFilter, SearchHit, VectorStore


class DenseRetriever(Retriever):
    name = "dense"

    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def retrieve(self, query: str, k: int, flt: MetadataFilter | None = None) -> list[SearchHit]:
        return self.store.search(self.embedder.embed_one(query), k, flt)
