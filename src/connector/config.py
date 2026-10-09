from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ConnectorConfig(BaseSettings):
    instagram_business_account_id: str = Field(validation_alias="IG_BUSINESS_ACCOUNT_ID")
    instagram_access_token: str = Field(validation_alias="IG_ACCESS_TOKEN")
    db_uri: str = Field(validation_alias="MONGO_URI")
    db_name: str = Field(validation_alias="MONGO_DB_NAME")
    graph_api_version: str = Field(validation_alias="GRAPH_API_VERSION")
    instagram_api_base_url: str = Field(default="https://graph.facebook.com", validation_alias="IG_API_BASE_URL")

    model_config = SettingsConfigDict(extra="ignore", env_file=".env", env_file_encoding="utf-8", populate_by_name=True)

@lru_cache()
def get_connector_config() -> ConnectorConfig:
    return ConnectorConfig()
