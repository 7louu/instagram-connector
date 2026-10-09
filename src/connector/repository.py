from hashlib import sha256
from typing import Any

from bson import ObjectId
from gridfs import GridFS, NoFile
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from connector.config import ConnectorConfig, get_connector_config
from connector.models.comments import Comment
from connector.models.post import ImageRef, Post
from connector.exceptions import MongoRepositoryError


class MongoRepository:
    def __init__(self, config: ConnectorConfig | None = None) -> None:
        config = config or get_connector_config()
        self.client = None
        try:
            self.client = MongoClient(
                config.db_uri, serverSelectionTimeoutMS=5000, tz_aware=True
            )
            self.db = self.client[config.db_name]
            self.posts = self.db["posts"]
            self.comments = self.db["comments"]
            self.images = GridFS(self.db, collection="images")
            self.comments.create_index("media_id")
            self.db["images.files"].create_index("metadata.sha256")
        except PyMongoError as exc:
            if self.client is not None:
                self.client.close()
            raise MongoRepositoryError("Could not initialize the MongoDB repository") from exc

    def save_post(self, post: Post) -> None:
        document = post.to_document()
        if document.get("image") is None:
            document.pop("image", None)
        self._upsert(self.posts, document)

    def save_comment(self, comment: Comment) -> None:
        self._upsert(self.comments, comment.to_document())

    def get_post(self, post_id: str) -> Post | None:
        try:
            document = self.posts.find_one({"_id": post_id})
        except PyMongoError as exc:
            raise MongoRepositoryError(f"Could not read post {post_id}") from exc
        if document is None:
            return None
        return Post(id=document.pop("_id"), **document)

    def get_comments(self, media_id: str) -> list[Comment]:
        try:
            documents = list(self.comments.find({"media_id": media_id}).sort("posted_at", 1))
        except PyMongoError as exc:
            raise MongoRepositoryError(f"Could not read comments for post {media_id}") from exc
        return [Comment(id=document.pop("_id"), **document) for document in documents]

    def save_image(self, content: bytes) -> ImageRef:
        checksum = sha256(content).hexdigest()
        try:
            existing = self.images.find_one({"metadata.sha256": checksum})
            image_id = (
                existing._id
                if existing is not None
                else self.images.put(content, metadata={"sha256": checksum})
            )
        except PyMongoError as exc:
            raise MongoRepositoryError("Could not save image to GridFS") from exc
        return ImageRef(gridfs_id=image_id, sha256=checksum, size=len(content))

    def get_image(self, image_id: ObjectId) -> bytes | None:
        try:
            return self.images.get(image_id).read()
        except NoFile:
            return None
        except PyMongoError as exc:
            raise MongoRepositoryError(f"Could not read image {image_id}") from exc

    def _upsert(self, collection: Collection, document: dict[str, Any]) -> None:
        document_id = document.pop("_id")
        collected_at = document.pop("collected_at")
        try:
            collection.update_one(
                {"_id": document_id},
                {"$set": document, "$setOnInsert": {"collected_at": collected_at}},
                upsert=True,
            )
        except PyMongoError as exc:
            raise MongoRepositoryError(
                f"Could not save {collection.name} document {document_id}"
            ) from exc

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "MongoRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
