from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any
from bson import ObjectId

def get_current_time() -> datetime:
    return datetime.now(timezone=datetime.timezone.utc)

class ImageRef(BaseModel):
    gridfs_id: ObjectId
    sha256: str
    size: int

class Post(BaseModel):
    id: str
    caption: str | None = None
    media_type: str
    media_url: str | None = None
    posted_at: datetime
    comments_count: int | None = None
    hashtags: list[str] | None = None
    image: ImageRef | None = None
    collected_at: datetime = Field(default_factory=get_current_time)

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "Post":
        return cls(
            id=raw["id"],
            caption=raw.get("caption"),
            media_type=raw["media_type"],
            media_url=raw.get("media_url"),
            posted_at=datetime.fromisoformat(raw["timestamp"]),
            comments_count=raw.get("comments_count"),
            hashtags=[tag.lstrip("#") for tag in raw.get("caption", "").split() if tag.startswith("#")],
        )

    def to_document(self) -> dict[str, Any]:
        doc = self.model_dump()
        doc["_id"] = doc.pop("id")
        return doc