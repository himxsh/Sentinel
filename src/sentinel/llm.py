import json

import boto3

from sentinel.config import get_settings


def plan(context: dict) -> dict:
    settings = get_settings()
    if settings.llm_backend == "bedrock":
        return _bedrock_plan(context, settings)
    return _fake_plan(context)


def _fake_plan(context: dict) -> dict:
    signal = context.get("signal", {})
    memories = context.get("memories", [])

    signal_text = str(signal).lower()
    memory_titles = " ".join(m.get("title", "") for m in memories).lower()
    haystack = signal_text + " " + memory_titles

    # ponytail: keyword heuristic; swap to real LLM when Claude unlocks
    if any(kw in haystack for kw in ["runaway", "p99", "latency", "connection pool", "full table scan"]):
        hypothesis = "Unoptimized analytical query consuming all connections and exhausting the pool"
        actions = [
            {"cmd": "cancel_query", "args": {"query_pattern": "full table scan"}, "destructive": False},
            {"cmd": "recommend_index", "args": {"table": "orders", "columns": ["status", "created_at"]}, "destructive": False},
        ]
        summary = "Cancelled runaway query, recommended covering index on orders(status, created_at)"
    elif any(kw in haystack for kw in ["hot range", "imbalance", "scatter"]):
        hypothesis = "Sequential UUIDs caused hot range with 10x QPS imbalance"
        actions = [
            {"cmd": "scatter_range", "args": {}, "destructive": False},
            {"cmd": "enable_random_uuids", "args": {}, "destructive": False},
        ]
        summary = "Scattered hot range, switched to random UUIDs to prevent recurrence"
    elif any(kw in haystack for kw in ["node down", "failure", "dead node", "under-replicated"]):
        hypothesis = "Single node failure from hardware error, ranges under-replicated"
        actions = [
            {"cmd": "decommission_node", "args": {"node_id": ""}, "destructive": True},
            {"cmd": "reprovision_node", "args": {}, "destructive": False},
        ]
        summary = "Decommissioned failed node and reprovisioned replacement"
    else:
        hypothesis = "Unknown signal pattern, initiating standard diagnostic"
        actions = [{"cmd": "investigate_metrics", "args": {"dashboard": "sql_overview"}, "destructive": False}]
        summary = "Gathering additional metrics for diagnosis"

    return {"hypothesis": hypothesis, "actions": actions, "summary": summary}


def _bedrock_plan(context: dict, settings) -> dict:
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    system_prompt = (
        "You are a database reliability engineer. Given an incident signal and relevant knowledge, "
        "return a JSON object with keys: hypothesis (str), actions (list of dicts with cmd/args/destructive), "
        "summary (str). Only non-destructive actions execute automatically."
    )
    user_msg = {
        "role": "user",
        "content": [{"text": f"Signal: {json.dumps(context.get('signal', {}))}\nMemories: {json.dumps(context.get('memories', []))}\nSkills: {json.dumps(context.get('skills', {}))}"}],
    }
    resp = client.converse(
        modelId=settings.bedrock_llm_model,
        system=[{"text": system_prompt}],
        messages=[user_msg],
        inferenceConfig={"maxTokens": 1024, "temperature": 0},
    )
    text = resp["output"]["message"]["content"][0]["text"]
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)
