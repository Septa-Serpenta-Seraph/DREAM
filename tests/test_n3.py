# tests/test_n3.py
import pytest
from dream.phases.n3_pruning import N3Pruning


def test_n3_identifies_stale_points():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "old memory", "timestamp": "2025-01-01T00:00:00"}, "vector": [0.1]*4},
                {"id": 2, "payload": {"text": "recent memory", "timestamp": "2026-11-06T00:00:00"}, "vector": [0.2]*4},
            ]
            return pts, None
        def delete_points(self, collection, ids):
            self.deleted = ids
            return True
    client = MockClient()
    n3 = N3Pruning(client, "test_collection", max_age_days=30, dry_run=True)
    result = n3.run()
    assert result["points_reviewed"] == 2
    assert result["stale_found"] == 1


def test_n3_dry_run_does_not_delete():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [{"id": 1, "payload": {"text": "old", "timestamp": "2025-01-01T00:00:00"}, "vector": [0.1]*4}]
            return pts, None
        def delete_points(self, collection, ids):
            raise AssertionError("Should not delete in dry run")
    client = MockClient()
    n3 = N3Pruning(client, "test_collection", max_age_days=30, dry_run=True)
    result = n3.run()
    assert result["dry_run"] is True
