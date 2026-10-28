"""Why a vector hit matched this alert.

ponytail: keyword overlap plus distance bands. Swap the sentence for an LLM
explanation when Bedrock is the default and the extra call is worth it.
"""

import re

_STOP = frozenset(
    "that this with from have been were they your when what into over than then them some "
    "select count where join cross".split()
)
_WORD = re.compile(r"[a-z0-9]{4,}")


def explain_matches(signal: dict, memories: list[dict]) -> list[dict]:
    signal_tokens = _tokens(_signal_text(signal))
    explained = []
    for memory in memories:
        title = str(memory.get("title") or "")
        content = str(memory.get("content") or "")
        source = str(memory.get("source") or "memory")
        overlap = sorted(signal_tokens & _tokens(f"{title} {content}"))[:8]
        distance = _distance(memory.get("distance"))
        band = _band(distance)
        dist_bit = f"{distance:.2f}" if distance is not None else "n/a"
        if overlap:
            shown = ", ".join(overlap[:4])
            why = (
                f"Shares {shown} with this alert. "
                f"Vector distance {dist_bit} puts it in the {band} band ({source})."
            )
        else:
            why = (
                f"No shared keywords. Kept as a {band} neighbor in the vector index, "
                f"distance {dist_bit} ({source})."
            )
        explained.append(
            {
                "title": title,
                "source": source,
                "distance": distance,
                "band": band,
                "overlap": overlap,
                "why": why,
            }
        )
    return explained


def _signal_text(signal: dict) -> str:
    parts = [str(signal.get("title") or ""), str(signal.get("cluster_ref") or "")]
    details = signal.get("details")
    if isinstance(details, dict):
        parts.extend(str(value) for value in details.values())
    elif signal:
        parts.append(str(signal))
    return " ".join(parts)


def _tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall(text.lower()) if word not in _STOP}


def _distance(value):
    if value is None:
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _band(distance) -> str:
    if distance is None:
        return "unknown"
    if distance < 0.15:
        return "near"
    if distance < 0.35:
        return "related"
    return "loose"
