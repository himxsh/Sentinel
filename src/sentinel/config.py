from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://root@localhost:26257/defaultdb?sslmode=disable"
    embeddings_backend: str = "fake"
    aws_region: str = "us-east-1"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
