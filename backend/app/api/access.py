"""Who may see which documents.

Shared documents are visible to every signed-in user. Private documents are visible
only to their owner and to admins.
"""

from __future__ import annotations

from app.db.repositories import DocumentRecord, UserRecord
from app.vectorstore.base import MetadataFilter


def can_view(user: UserRecord, rec: DocumentRecord) -> bool:
    return user.role == "admin" or rec.visibility == "shared" or rec.owner_id == user.id


def search_filter(user: UserRecord, collection: str | None = None) -> MetadataFilter | None:
    flt: MetadataFilter = {}
    if collection:
        flt["collection"] = collection
    if user.role != "admin":
        # Chunks indexed before visibility existed carry no tag and count as shared.
        flt["$or"] = [{"visibility": "shared"}, {"visibility": None}, {"owner_id": user.id}]
    return flt or None
