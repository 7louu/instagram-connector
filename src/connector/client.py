from connector.config import ConnectorConfig, get_connector_config
from connector.exceptions import InstagramAPIError
from urllib.parse import urlparse
from typing import Any
import requests

class InstagramClient:
    def __init__(
        self,
        config: ConnectorConfig | None = None,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.config = config or get_connector_config()
        self.session = session or requests.Session()
        self.timeout = timeout
        self.base_url = (
            f"{self.config.instagram_api_base_url.rstrip('/')}/"
            f"{self.config.graph_api_version.strip('/')}"
        )

    def fetch_posts(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            f"{self.base_url}/{self.config.instagram_user_id}/media",
            {
                "fields": (
                    "id,caption,media_type,media_url,thumbnail_url,timestamp,"
                    "permalink,comments_count,children{ id,media_type,media_url,thumbnail_url }"
                ),
                "limit": 100,
            },
        )

    def fetch_comments(self, media_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            f"{self.base_url}/{media_id}/comments",
            {"fields": "id,text,timestamp,username,like_count", "limit": 100},
        )

    def download_media(self, media_url: str) -> bytes:
        if urlparse(media_url).scheme != "https":
            raise InstagramAPIError("Instagram media URL must use HTTPS")
        response = self._request(media_url)
        return response.content

    def _fetch_all(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        next_url: str | None = url
        next_params: dict[str, Any] | None = {
            **params,
            "access_token": self.config.instagram_access_token,
        }

        while next_url:
            response = self._request(next_url, params=next_params)
            try:
                payload = response.json()
            except ValueError as exc:
                raise InstagramAPIError("Instagram returned an invalid JSON response") from exc

            if not isinstance(payload, dict):
                raise InstagramAPIError("Instagram returned an unexpected response")
            if "error" in payload:
                error = payload["error"]
                message = error.get("message", "Instagram API request failed") if isinstance(error, dict) else str(error)
                raise InstagramAPIError(message)
            data = payload.get("data")
            if not isinstance(data, list):
                raise InstagramAPIError("Instagram response is missing its data list")
            results.extend(item for item in data if isinstance(item, dict))

            paging = payload.get("paging") or {}
            next_url = paging.get("next") if isinstance(paging, dict) else None
            next_params = None

        return results

    def _request(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            response = exc.response
            if response is not None:
                try:
                    payload = response.json()
                    error = payload.get("error", {}) if isinstance(payload, dict) else {}
                    message = error.get("message") if isinstance(error, dict) else None
                    if message:
                        raise InstagramAPIError(message) from exc
                except ValueError:
                    pass
            raise InstagramAPIError(f"Instagram request failed: {exc}") from exc
