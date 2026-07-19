from sentinel.config import get_settings
from sentinel.embeddings import embed


def test_fake_embed_length():
    get_settings.cache_clear()
    v = embed("hello")
    assert len(v) == 1024


def test_fake_embed_deterministic():
    get_settings.cache_clear()
    assert embed("hello") == embed("hello")


def test_fake_embed_different_inputs():
    get_settings.cache_clear()
    assert embed("hot range imbalance") != embed("runaway query p99")
