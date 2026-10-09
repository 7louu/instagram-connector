# Instagram connector

This connector uses the Instagram API with Facebook Login. The connected Instagram
account must be a Business or Creator account linked to a Facebook Page. The
hashtag search feature also needs the appropriate public content access in the
Meta app.

## Setup

Requires Python 3.10 or later. Install the connector with:

```shell
python -m pip install -e .
```

Copy `.env.example` to `.env`, then set `IG_BUSINESS_ACCOUNT_ID` to the Instagram professional
account ID and `IG_ACCESS_TOKEN` to its Facebook Page access token. Account
media access uses `pages_show_list`, `pages_read_engagement`, and
`instagram_basic`; reading its comments also needs `instagram_manage_comments`.
Hashtag search uses `instagram_basic` and Meta's public content access feature.
Use the access token and IDs you obtained from Meta's Graph API tools. Do not
commit `.env`.

Start the Docker service with:

```shell
docker compose up -d mongo
```

Set `MONGO_URI` and `MONGO_DB_NAME` in `.env`. A local Compose URI usually looks
like `mongodb://USER:PASSWORD@localhost:27017/?authSource=admin`.

## Sync posts

Search by topic label and one or more explicit hashtags, while also fetching all
posts from the connected account:

```shell
instagram-connector --topic coffee --hashtag coffee --hashtag cafe
```

`--topic` labels the collection run and the saved posts; it does not generate
hashtags. Supplying the hashtags explicitly keeps the search local and avoids a
paid text-generation service. Public hashtag results default to recent posts;
use `--hashtag-order top` to select top posts.

To fetch only the connected account's posts and their comments:

```shell
instagram-connector --source account
```

To fetch only public posts found by hashtags:

```shell
instagram-connector --source hashtags --topic coffee --hashtag coffee
```

To verify if data has been saved correctly:

```shell
docker exec -it your_database_name mongosh -u "your_mongo_user" -p authenticationDatabase admin
```
Enter your password then run commands to find or count documents.


Hashtag search is restricted by Meta's access and usage limits. In particular,
an Instagram professional account may search at most 30 distinct hashtags in a
rolling seven-day period. Re-running this command does not use a paid API tier,
but the API may reject a hashtag search if the Meta app lacks public-content
access.

