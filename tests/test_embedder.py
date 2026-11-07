# tests/test_embedder.py
import pytest
from dream.embedder import FastEmbedEmbedder


def test_embedder_init():
    embedder = FastEmbedEmbedder(
        python_path="/mnt/data/fe-venv/bin/python",
        script_path="/home/adora/.hermes/scripts/embed_fastembed_local.py",
    )
    assert embedder.python_path == "/mnt/data/fe-venv/bin/python"


def test_embedder_embed_returns_vectors(monkeypatch):
    embedder = FastEmbedEmbedder(
        python_path="/mnt/data/fe-venv/bin/python",
        script_path="/home/adora/.hermes/scripts/embed_fastembed_local.py",
    )
    # Mock subprocess
    import subprocess
    class FakeProc:
        def __init__(self):
            self.stdin = self
            self.stdout = self
            self._responses = ['{"id": 1, "vectors": [[0.1, 0.2, 0.3]], "error": null}\n']
            self._idx = 0
        def write(self, data):
            pass
        def flush(self):
            pass
        def readline(self):
            resp = self._responses[self._idx]
            self._idx += 1
            return resp
        def terminate(self):
            pass
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: FakeProc())
    vectors = embedder.embed(["test text"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 3
