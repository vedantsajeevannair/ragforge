"""Retriever interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.vectorstore.base import MetadataFilter, SearchHit


class Retriever(ABC):
    name: str = "base"

    @abstractmethod
    def retrieve(self, query: str, k: int, flt: MetadataFilter | None = None) -> list[SearchHit]:
        ...
