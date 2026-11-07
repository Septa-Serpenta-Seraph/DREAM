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

    assert report["phases_run"] == ["n1", "n2", "n3", "rem"]
    assert set(report["phases"].keys()) == {"n1", "n2", "n3", "rem"}
    assert len(report["results"]) == 4
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
