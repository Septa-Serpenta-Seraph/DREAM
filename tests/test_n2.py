# tests/test_n2.py
import pytest
from dream.phases.n2_spindle import N2Spindle


def test_n2_finds_clusters():
    """N2 should identify clusters of similar memories."""
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "memory one"}, "vector": [1.0, 0.0, 0.0, 0.0]},
                {"id": 2, "payload": {"text": "memory two"}, "vector": [0.9, 0.1, 0.0, 0.0]},
                {"id": 3, "payload": {"text": "unrelated"}, "vector": [0.0, 0.0, 1.0, 0.0]},
            ]
            return pts, None
        def search(self, collection, vector, limit=5, score_threshold=0.0):
            # Return points 1 and 2 as neighbors (they're close together)
            return [
                {"id": 2, "score": 0.95, "payload": {"text": "memory two"}},
            ]
    client = MockClient()
    n2 = N2Spindle(client, "test_collection", dry_run=True)
    result = n2.run()
    assert result["points_reviewed"] == 3
    assert result["clusters_found"] >= 1


def test_n2_dry_run_does_not_upsert():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [{"id": 1, "payload": {"text": "t"}, "vector": [0.1]*4}]
            return pts, None
        def upsert_points(self, collection, points):
            raise AssertionError("Should not upsert in dry run")
    client = MockClient()
    n2 = N2Spindle(client, "test_collection", dry_run=True)
    result = n2.run()
    assert result["dry_run"] is True
