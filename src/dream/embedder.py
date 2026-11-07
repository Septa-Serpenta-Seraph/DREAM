"""Fastembed embedding via subprocess daemon."""

import json
import subprocess


class FastEmbedEmbedder:
    def __init__(self, python_path, script_path):
        self.python_path = python_path
        self.script_path = script_path
        self._proc = None

    def _start(self):
        if self._proc is None:
            self._proc = subprocess.Popen(
                [self.python_path, self.script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )

    def embed(self, texts):
        self._start()
        req = {"id": 1, "texts": texts}
        self._proc.stdin.write(json.dumps(req) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        resp = json.loads(line)
        if resp.get("error"):
            raise RuntimeError(resp["error"])
        return resp["vectors"]

    def close(self):
        if self._proc:
            self._proc.terminate()
            self._proc = None
