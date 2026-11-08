# tests/test_n2.py
import pytest
from dream.phases.n2_spindle import N2Spindle


class MockDreamStore:
    def __init__(self):
        self.written = []

    def write_artifact(self, kind, title, text, meta=None):
        self.written.append((kind, title, text, meta))
        return "artifact-2"


def make_client():
    class MockClient:
        def __init__(self):
            self.upserts = []

        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "memory one"}, "vector": [1.0, 0.0, 0.0, 0.0]},
                {"id": 2, "payload": {"text": "memory two"}, "vector": [0.9, 0.1, 0.0, 0.0]},
                {"id": 3, "payload": {"text": "unrelated"}, "vector": [0.0, 0.0, 1.0, 0.0]},
            ]
            return pts, None

        def search(self, collection, vector, limit=5, score_threshold=0.0):
            return [
                {"id": 2, "score": 0.95, "payload": {"text": "memory two"}},
            ]

        def upsert_points(self, collection, points):
            self.upserts.append((collection, points))
            return True

    return MockClient()


def test_n2_finds_clusters():
    """N2 should identify clusters of similar memories."""
    n2 = N2Spindle(make_client(), "test_collection")
    result = n2.run()
    assert result["points_reviewed"] == 3
    assert result["clusters_found"] >= 1
    assert result["archive_modified"] is False


def test_n2_never_writes_to_memory_collection():
    """Cluster tags used to be written back into the archive. Never again."""
    for dry_run in (True, False):
        client = make_client()
        n2 = N2Spindle(client, "test_collection", dry_run=dry_run)
        n2.run()
        assert client.upserts == []


def test_n2_journals_cluster_map_to_dream_store():
    store = MockDreamStore()
    n2 = N2Spindle(make_client(), "test_collection", dream_store=store)
    result = n2.run()
    assert len(store.written) == 1
    kind, title, text, meta = store.written[0]
    assert kind == "n2_clusters"
    assert "clusters" in meta and meta["clusters"][0]["members"]
    assert result["artifact_id"] == "artifact-2"
