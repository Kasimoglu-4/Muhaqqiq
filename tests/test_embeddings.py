from muhaqqiq.embeddings import EmbeddingIndex, hash_embed


def test_hash_embed_normalized():
    v = hash_embed("انما الاعمال بالنيات")
    assert len(v) == 384
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_hash_embed_stable():
    assert hash_embed("abc") == hash_embed("abc")


def test_disabled_query_empty():
    idx = EmbeddingIndex()
    assert idx.query("test") == []
