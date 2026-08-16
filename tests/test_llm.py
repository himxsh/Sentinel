import json

from sentinel.llm import _parse_json


def test_parse_json_fenced():
    obj = {"hypothesis": "h", "actions": [], "summary": "s"}
    text = "```json\n" + json.dumps(obj) + "\n```"
    assert _parse_json(text) == obj


def test_parse_json_prose_wrapped():
    obj = {"hypothesis": "h", "actions": [], "summary": "s"}
    text = "Here is the plan: " + json.dumps(obj) + " Hope that helps!"
    assert _parse_json(text) == obj