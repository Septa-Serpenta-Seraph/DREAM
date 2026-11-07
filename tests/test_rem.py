# tests/test_rem.py
import pytest
from dream.phases.n4_rem import N4REM


def test_rem_produces_report():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "memory one", "role": "user"}, "vector": [0.1]*4},
                {"id": 2, "payload": {"text": "memory two", "role": "assistant"}, "vector": [0.2]*4},
            ]
            return pts, None
        def get_point_count(self, name):
            return 2
    client = MockClient()
    rem = N4REM(client, "test_collection", dry_run=True)
    result = rem.run()
    assert result["phase"] == "rem"
    assert result["points_reviewed"] == 2
    assert "summary" in result


def test_rem_dry_run():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            return [], None
        def get_point_count(self, name):
            return 0
    client = MockClient()
    rem = N4REM(client, "test_collection", dry_run=True)
    result = rem.run()
    assert result["dry_run"] is True
    assert result["points_reviewed"] == 0
