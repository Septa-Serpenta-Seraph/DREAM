# tests/test_storyweave.py
import pytest
from dream.phases.storyweave import Storyweave


def test_storyweave_produces_story():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            pts = [
                {"id": 1, "payload": {"text": "memory one", "role": "user", "timestamp": "2026-11-07T00:00:00"}, "vector": [0.1] * 4},
                {"id": 2, "payload": {"text": "memory two", "role": "assistant", "timestamp": "2026-11-07T01:00:00"}, "vector": [0.2] * 4},
            ]
            return pts, None

    client = MockClient()
    sw = Storyweave(client, "test_collection", dry_run=True)
    result = sw.weave({"n1": {"duplicates_found": 1}, "n2": {"clusters_found": 2}, "n3": {"stale_found": 0}})
    assert result["phase"] == "storyweave"
    assert "story" in result
    assert len(result["story"]) > 0
    assert result["memories_sampled"] == 2
    assert result["dry_run"] is True


def test_storyweave_dry_run():
    class MockClient:
        def scroll_points(self, collection, limit=100, offset=None, **kw):
            return [], None

    client = MockClient()
    sw = Storyweave(client, "test_collection", dry_run=True)
    result = sw.weave({})
    assert result["phase"] == "storyweave"
    assert result["memories_sampled"] == 0
