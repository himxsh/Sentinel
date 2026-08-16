import boto3

from sentinel import llm
from sentinel.config import get_settings
from sentinel.embeddings import embed
from sentinel.memory import store_knowledge, log_event


def write_postmortem(conn, incident_id, context: dict) -> dict:
    pm = llm.postmortem(context)
    emb = embed(pm["content"])
    kid = store_knowledge(
        conn,
        source="postmortem",
        title=pm["title"],
        content=pm["content"],
        embedding=emb,
        metadata={"incident_id": incident_id},
    )
    detail = {"postmortem_id": kid, "title": pm["title"]}
    settings = get_settings()
    if settings.s3_bucket:
        key = f"postmortems/{incident_id}.md"
        try:
            boto3.client("s3", region_name=settings.aws_region).put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=pm["content"],
                ContentType="text/markdown",
            )
            detail["s3_key"] = key
        except Exception:
            pass  # ponytail: soft-fail — never break the agent loop; add retry/alerting if uploads start mattering
    log_event(conn, incident_id, "agent", "observation", detail)
    return {**pm, "knowledge_id": kid}
