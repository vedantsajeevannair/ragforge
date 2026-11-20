"""Lexical retriever wrapping a BM25 index."""

from app.retrieval.base import Retriever
from app.retrieval.bm25 import BM25Index
from app.vectorstore.base import MetadataFilter, SearchHit


class LexicalRetriever(Retriever):
    name = "bm25"

    def __init__(self, index: BM25Index) -> None:
        self.index = index

    def retrieve(self, query: str, k: int, flt: MetadataFilter | None = None) -> list[SearchHit]:
        return self.index.search(query, k, flt)
