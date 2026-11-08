# tests/test_n1.py
import pytest
from dream.phases.n1_consolidation import N1Consolidation


class MockDreamStore:
    def __init__(self):
        self.written = []

    def write_artifact(self, kind, title, text, meta=None):
        self.written.append((kind, title, text))
        return "artifact-1"


def make_points():
    return [
        {"id": 1, "payload": {"text": "Adora is tired"}, "vector": [0.1] * 4},
        {"id": 2, "payload": {"text": "Adora is tired"}, "vector": [0.1] * 4},
        {"id": 3, "payload": {"text": "Completely different text"}, "vector": [0.9] * 4},
    ]


def test_n1_finds_duplicates():
    """N1 should identify duplicate points."""

    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            if offset is None:
                return make_points(), None
            return [], None

        def delete_points(self, collection, ids):
            raise AssertionError("N1 must never delete from the archive")

    client = MockClient()
    n1 = N1Consolidation(client, "test_collection")
    result = n1.run()
    assert result["duplicates_found"] == 1
    assert result["points_reviewed"] == 3
    assert result["duplicates_removed"] == 0
    assert result["archive_modified"] is False
    assert result["duplicate_samples"][0]["id"] == 2
    assert result["duplicate_samples"][0]["kept"] == 1


def test_n1_never_deletes_even_in_live_mode():
    """The 53-memory incident: N1 must be delete-proof regardless of dry_run."""

    class MockClient:
        def __init__(self):
            self.deleted = None

        def scroll_points(self, collection, limit=100, offset=None, **kw):
            if offset is None:
                return [
                    {"id": 1, "payload": {"text": "same"}, "vector": [0.1] * 4},
                    {"id": 2, "payload": {"text": "same"}, "vector": [0.1] * 4},
                ], None
            return [], None

        def delete_points(self, collection, ids):
            self.deleted = ids
            return True

    client = MockClient()
    for dry_run in (True, False):
        n1 = N1Consolidation(client, "test_collection", dry_run=dry_run)
        result = n1.run()
        assert result["duplicates_found"] == 1
        assert result["duplicates_removed"] == 0
    assert client.deleted is None


def test_n1_journals_duplicates_to_dream_store():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            if offset is None:
                return make_points(), None
            return [], None

    store = MockDreamStore()
    n1 = N1Consolidation(MockClient(), "test_collection", dream_store=store)
    result = n1.run()
    assert len(store.written) == 1
    kind, title, text = store.written[0]
    assert kind == "n1_duplicates"
    assert "1 exact duplicates" in title
    assert result["artifact_id"] == "artifact-1"
