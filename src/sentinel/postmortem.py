from sentinel import llm
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
    log_event(conn, incident_id, "agent", "observation", {
        "postmortem_id": kid,
        "title": pm["title"],
    })
    return {**pm, "knowledge_id": kid}
