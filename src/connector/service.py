from dataclasses import dataclass, field
from typing import Any

from connector.client import InstagramClient
from connector.exceptions import InstagramAPIError
from connector.models.comments import Comment
from connector.models.post import Post
from connector.repository import MongoRepository


@dataclass
class _CollectedPost:
    data: dict[str, Any] = field(default_factory=dict)
    sources: set[str] = field(default_factory=set)
    hashtags: set[str] = field(default_factory=set)


@dataclass
class SyncResult:
    posts: int = 0
    comments: int = 0
    images: int = 0


class InstagramSyncService:
    def __init__(self, client: InstagramClient, repository: MongoRepository) -> None:
        self.client = client
        self.repository = repository

    def sync(
        self,
        *,
        topic: str | None = None,
        hashtags: list[str] | None = None,
        include_account_posts: bool = True,
        include_hashtag_posts: bool = True,
        hashtag_order: str = "recent",
    ) -> SyncResult:
        normalized_hashtags = {
            tag.strip().lstrip("#").strip().lower() for tag in hashtags or []
        }
        hashtags = sorted(tag for tag in normalized_hashtags if tag)
        if len(hashtags) > 30:
            raise ValueError("A sync can search at most 30 unique hashtags")
        if not include_account_posts and not include_hashtag_posts:
            raise ValueError("Select at least one post source")
        if include_hashtag_posts and not hashtags:
            raise ValueError("Provide at least one hashtag for hashtag search")
        if topic is not None and not topic.strip():
            raise ValueError("Topic cannot be empty")
        if topic is not None:
            topic = topic.strip()

        posts: dict[str, _CollectedPost] = {}

        def collect(raw: dict[str, Any], source: str, hashtag: str | None = None) -> None:
            post_id = raw.get("id")
            if not post_id:
                raise InstagramAPIError("Instagram returned a post without an ID")
            record = posts.setdefault(post_id, _CollectedPost())
            record.data.update({key: value for key, value in raw.items() if value is not None})
            record.sources.add(source)
            if hashtag:
                record.hashtags.add(hashtag)

        if include_account_posts:
            for raw in self.client.fetch_posts():
                collect(raw, "account")

        if include_hashtag_posts:
            for hashtag in hashtags:
                hashtag_id = self.client.search_hashtag(hashtag)
                if hashtag_id is None:
                    continue
                for raw in self.client.fetch_hashtag_media(hashtag_id, order=hashtag_order):
                    collect(raw, "hashtag", hashtag)

        result = SyncResult()
        account_post_ids: list[str] = []
        for post_id, record in posts.items():
            post = Post.from_api(
                record.data,
                topic=topic,
                sources=sorted(record.sources),
                matched_hashtags=sorted(record.hashtags),
            )
            if post.media_type == "IMAGE" and post.media_url:
                post.image = self.repository.save_image(self.client.download_media(post.media_url))
                result.images += 1
            for child in post.children:
                if child.media_type == "IMAGE" and child.media_url:
                    child.image = self.repository.save_image(self.client.download_media(child.media_url))
                    result.images += 1

            self.repository.save_post(post)
            result.posts += 1
            if "account" in record.sources:
                account_post_ids.append(post_id)

        for post_id in account_post_ids:
            for raw_comment in self.client.fetch_comments(post_id):
                self.repository.save_comment(Comment.from_api(raw_comment, media_id=post_id))
                result.comments += 1

        return result
