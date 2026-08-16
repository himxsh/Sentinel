import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentinel.config import get_settings


@pytest.fixture(autouse=True)
def _fake_backends(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.setenv("EMBEDDINGS_BACKEND", "fake")
    get_settings.cache_clear()