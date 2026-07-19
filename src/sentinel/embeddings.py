import hashlib
import json
import random

import boto3

from sentinel.config import get_settings


def embed(text: str) -> list[float]:
    settings = get_settings()
    if settings.embeddings_backend == "bedrock":
        return _bedrock_embed(text, settings)
    return _fake_embed(text)


def _fake_embed(text: str) -> list[float]:
    # ponytail: hash-based fake vectors; switch EMBEDDINGS_BACKEND=bedrock + Titan v2 for real semantic recall
    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.random() for _ in range(1024)]


def _bedrock_embed(text: str, settings) -> list[float]:
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    body = json.dumps({"inputText": text, "dimensions": 1024})
    resp = client.invoke_model(
        modelId=settings.bedrock_embed_model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    return json.loads(resp["body"].read())["embedding"]
