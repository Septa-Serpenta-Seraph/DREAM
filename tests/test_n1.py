# tests/test_n1.py
import pytest
from dream.phases.n1_consolidation import N1Consolidation


def test_n1_finds_duplicates():
    """N1 should identify duplicate or near-duplicate points."""
    # Mock Qdrant client
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            if offset is None:
                pts = [
                    {"id": 1, "payload": {"text": "Adora is tired"}, "vector": [0.1]*4},
                    {"id": 2, "payload": {"text": "Adora is tired"}, "vector": [0.1]*4},
                    {"id": 3, "payload": {"text": "Completely different text"}, "vector": [0.9]*4},
                ]
                return pts, None
            return [], None
        def delete_points(self, collection, ids):
            self.deleted = ids
            return True
    client = MockClient()
    n1 = N1Consolidation(client, "test_collection", dry_run=True)
    result = n1.run()
    assert result["duplicates_found"] == 1
    assert result["points_reviewed"] == 3


def test_n1_dry_run_does_not_delete():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "same"}, "vector": [0.1]*4},
                {"id": 2, "payload": {"text": "same"}, "vector": [0.1]*4},
            ]
            return pts, None
        def delete_points(self, collection, ids):
            raise AssertionError("Should not delete in dry run")
    client = MockClient()
    n1 = N1Consolidation(client, "test_collection", dry_run=True)
    result = n1.run()
    assert result["duplicates_found"] == 1
