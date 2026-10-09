import argparse
import sys

from connector.client import InstagramClient
from connector.exceptions import InstagramAPIError, MongoRepositoryError
from connector.repository import MongoRepository
from connector.service import InstagramSyncService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Instagram posts and save them to MongoDB.")
    parser.add_argument(
        "--source",
        choices=("account", "hashtags", "both"),
        default="both",
        help="Fetch the connected account's posts, hashtag posts, or both (default: both).",
    )
    parser.add_argument("--topic", help="Topic label to save with discovered posts.")
    parser.add_argument(
        "--hashtag",
        action="append",
        default=[],
        help="Hashtag to search (repeat for more than one; omit the #).",
    )
    parser.add_argument(
        "--hashtag-order",
        choices=("recent", "top"),
        default="recent",
        help="Which public posts to fetch for each hashtag (default: recent).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    uses_hashtags = args.source in {"hashtags", "both"}
    if uses_hashtags and not args.hashtag:
        parser.error("--source hashtags or both requires at least one --hashtag")
    if uses_hashtags and not args.topic:
        parser.error("--source hashtags or both requires --topic")
    if args.source == "account" and args.hashtag:
        parser.error("--hashtag can only be used with --source hashtags or both")

    client = InstagramClient()
    try:
        with MongoRepository() as repository:
            result = InstagramSyncService(client, repository).sync(
                topic=args.topic,
                hashtags=args.hashtag,
                include_account_posts=args.source in {"account", "both"},
                include_hashtag_posts=uses_hashtags,
                hashtag_order=args.hashtag_order,
            )
        print(
            f"Saved {result.posts} posts, {result.images} images, "
            f"and {result.comments} account-post comments."
        )
        return 0
    except (InstagramAPIError, MongoRepositoryError) as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
