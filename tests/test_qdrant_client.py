# tests/test_qdrant_client.py
import pytest
from dream.qdrant_client import QdrantClient


def test_qdrant_client_init():
    client = QdrantClient(base_url="http://localhost:6333")
    assert client.base_url == "http://localhost:6333"


def test_qdrant_client_collection_exists(monkeypatch):
    client = QdrantClient(base_url="http://localhost:6333")
    # Mock the HTTP response
    import json
    class FakeResponse:
        def __init__(self, data):
            self._data = data
        def read(self):
            return json.dumps(self._data).encode()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr("urllib.request.urlopen", lambda req, **kw: FakeResponse({"result": {"status": "green", "points_count": 5}}))
    assert client.collection_exists("test_collection") is True


def test_qdrant_client_collection_not_exists(monkeypatch):
    client = QdrantClient(base_url="http://localhost:6333")
    import urllib.error
    def raise_404(req, **kw):
        raise urllib.error.HTTPError(req.full_url, 404, "Not found", {}, None)
    monkeypatch.setattr("urllib.request.urlopen", raise_404)
    assert client.collection_exists("nonexistent") is False
