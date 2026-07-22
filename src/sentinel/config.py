from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://root@localhost:26257/defaultdb?sslmode=disable"
    embeddings_backend: str = "fake"
    llm_backend: str = "fake"
    aws_region: str = "us-east-1"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"
    bedrock_llm_model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    sentinel_read_user: str = ""
    sentinel_read_password: str = ""
    ccloud_bin: str = "ccloud"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
