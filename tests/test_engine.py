# tests/test_engine.py
import pytest
from dream.engine import DreamEngine


def test_engine_runs_all_phases():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "memory one", "role": "user"}, "vector": [0.1] * 4},
                {"id": 2, "payload": {"text": "memory two", "role": "assistant"}, "vector": [0.2] * 4},
            ]
            return pts, None

        def delete_points(self, collection, ids):
            return True

        def upsert_points(self, collection, points):
            return True

        def get_point_count(self, name):
            return 2

    client = MockClient()
    engine = DreamEngine(client=client, collection="test_collection", dry_run=True)
    report = engine.dream()

    assert report["phases_run"] == ["n1", "n2", "n3", "rem", "storyweave"]
    assert set(report["phases"].keys()) == {"n1", "n2", "n3", "rem", "storyweave"}
    assert len(report["results"]) == 5
    for result in report["results"]:
        assert "phase" in result


def test_engine_dry_run_propagates():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            return [], None

        def get_point_count(self, name):
            return 0

    client = MockClient()
    engine = DreamEngine(client=client, collection="test_collection", dry_run=True)
    report = engine.dream(phases=["n1", "rem"])

    assert report["dry_run"] is True
    assert report["phases_run"] == ["n1", "rem"]
    assert report["n1"]["dry_run"] is True
    assert report["rem"]["dry_run"] is True


def test_engine_archive_is_untouchable_even_in_live_mode():
    """The whole engine, run 'live', must never write to the memory collection.
    Journal writes go only to the dream collection."""
    writes = []

    class TrackingClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "same", "role": "user",
                                      "timestamp": "2020-01-01T00:00:00Z"}, "vector": [0.1] * 4},
                {"id": 2, "payload": {"text": "same", "role": "assistant",
                                      "timestamp": "2020-01-01T00:00:00Z"}, "vector": [0.1] * 4},
            ]
            return pts, None

        def search(self, collection, vector, limit=5, score_threshold=0.0):
            return [{"id": 2, "score": 0.99, "payload": {"text": "same"}}]

        def upsert_points(self, collection, points):
            writes.append(("upsert", collection))
            return True

        def delete_points(self, collection, ids):
            writes.append(("delete", collection))
            return True

        def get_point_count(self, name):
            return 2

        def collection_exists(self, name):
            return True

        def create_collection(self, name, size=384, distance="Cosine"):
            writes.append(("create", name))
            return True

    class FakeEmbedder:
        def embed(self, texts):
            return [[0.1] * 384 for _ in texts]

        def close(self):
            pass

    client = TrackingClient()
    engine = DreamEngine(
        client=client, collection="memory_archive",
        dry_run=False,  # "live mode" — must still be read-only on the archive
        dream_collection="dream_journal",
    )
    engine.embedder = FakeEmbedder()
    engine.dream_store.embedder = FakeEmbedder()
    report = engine.dream(phases=["n1", "n2", "n3", "storyweave"])

    assert report["archive_modified"] is False
    for kind, coll in writes:
        assert coll == "dream_journal", f"illegal write to {coll} ({kind})"
    assert report["dream_store"]["artifacts_written"] >= 1
    # n1 found the duplicate but removed nothing
    assert report["n1"]["duplicates_found"] == 1
    assert report["n1"]["duplicates_removed"] == 0
    # n2 clustered but tagged nothing in the archive
    assert report["n2"]["archive_modified"] is False
    # the narrative was journaled, not stored in the archive
    assert report["storyweave"].get("artifact_id") is not None
