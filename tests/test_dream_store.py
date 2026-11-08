# tests/test_dream_store.py
import pytest
from dream.dream_store import DreamStore


class MockEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return [[0.1] * 384 for _ in texts]


class MockClient:
    def __init__(self):
        self.created = []
        self.upserts = []

    def collection_exists(self, name):
        return name in self.created

    def create_collection(self, name, size=384, distance="Cosine"):
        self.created.append((name, size, distance))
        return True

    def upsert_points(self, collection, points):
        self.upserts.append((collection, points))
        return True


def test_store_creates_collection_lazily():
    client = MockClient()
    embedder = MockEmbedder()
    store = DreamStore(client, "dream_journal", embedder)
    assert client.created == []  # nothing created before first write
    store.write_artifact("storyweave", "a dream", "the serpent dreamed of gardens")
    assert client.created == [("dream_journal", 384, "Cosine")]
    # second write does not re-create
    store.write_artifact("n1_duplicates", "0 dups", "none")
    assert len(client.created) == 1


def test_store_writes_embedded_artifact():
    client = MockClient()
    embedder = MockEmbedder()
    store = DreamStore(client, "dream_journal", embedder)
    pid = store.write_artifact(
        "n2_clusters", "3 clusters", "cluster text", {"collection": "mem"}
    )
    assert pid is not None
    coll, points = client.upserts[0]
    assert coll == "dream_journal"
    assert len(points) == 1
    assert points[0]["id"] == pid
    assert len(points[0]["vector"]) == 384
    payload = points[0]["payload"]
    assert payload["kind"] == "n2_clusters"
    assert payload["title"] == "3 clusters"
    assert payload["text"] == "cluster text"
    assert payload["collection"] == "mem"
    assert "timestamp" in payload
    assert store.artifacts_written == 1
    assert store.status()["artifacts_written"] == 1


def test_store_disabled_without_embedder():
    client = MockClient()
    store = DreamStore(client, "dream_journal", None)
    assert not store.enabled
    assert store.write_artifact("k", "t", "text") is None
    assert client.upserts == []
    assert store.skipped == 1


def test_store_never_raises_on_embedder_failure():
    class ExplodingEmbedder:
        def embed(self, texts):
            raise RuntimeError("daemon died")

    client = MockClient()
    store = DreamStore(client, "dream_journal", ExplodingEmbedder())
    assert store.write_artifact("k", "t", "text") is None
    assert store.skipped == 1
    assert store.artifacts_written == 0
