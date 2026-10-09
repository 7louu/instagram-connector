from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any

def get_current_time() -> datetime:
    return datetime.now(timezone=datetime.timezone.utc)

class Comment(BaseModel):
    id: str
    media_id: str
    text: str
    posted_at: datetime | None = None
    username: str | None = None
    like_count: int | None = None
    collected_at: datetime = Field(default_factory=get_current_time)

    @classmethod
    def from_api(cls, raw: dict[str, Any], media_id: str) -> "Comment":
        return cls(
            id=raw["id"],
            media_id=media_id,
            text=raw.get("text"),
            posted_at=datetime.fromisoformat(raw["timestamp"]) if "timestamp" in raw else None,
            username=raw.get("username"),
            like_count=raw.get("like_count"),
        )

    def to_document(self) -> dict[str, Any]:
        doc = self.model_dump()
        doc["_id"] = doc.pop("id")
        return doc