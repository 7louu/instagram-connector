from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Any
from bson import ObjectId

def get_current_time() -> datetime:
    return datetime.now(timezone.utc)

class ImageRef(BaseModel):
    gridfs_id: ObjectId
    sha256: str
    size: int

    model_config = {"arbitrary_types_allowed": True}


class PostMedia(BaseModel):
    id: str
    media_type: str
    media_url: str | None = None
    thumbnail_url: str | None = None
    image: ImageRef | None = None

class Post(BaseModel):
    id: str
    caption: str | None = None
    media_type: str
    media_url: str | None = None
    posted_at: datetime
    comments_count: int | None = None
    hashtags: list[str] | None = None
    image: ImageRef | None = None
    children: list[PostMedia] = Field(default_factory=list)
    topic: str | None = None
    sources: list[str] = Field(default_factory=list)
    matched_hashtags: list[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=get_current_time)

    @classmethod
    def from_api(
        cls,
        raw: dict[str, Any],
        *,
        topic: str | None = None,
        sources: list[str] | None = None,
        matched_hashtags: list[str] | None = None,
    ) -> "Post":
        children = raw.get("children") or {}
        child_data = children.get("data", []) if isinstance(children, dict) else []
        return cls(
            id=raw["id"],
            caption=raw.get("caption"),
            media_type=raw["media_type"],
            media_url=raw.get("media_url"),
            posted_at=datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00")),
            comments_count=raw.get("comments_count"),
            hashtags=[tag[1:].rstrip(".,!?;:") for tag in (raw.get("caption") or "").split() if tag.startswith("#")],
            children=child_data,
            topic=topic,
            sources=sources or [],
            matched_hashtags=matched_hashtags or [],
        )

    def to_document(self) -> dict[str, Any]:
        doc = self.model_dump()
        doc["_id"] = doc.pop("id")
        return doc
