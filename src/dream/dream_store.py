"""DreamStore — the dream's own journal.

DREAM is read-only toward the memory archive: it never modifies, tags,
archives, or deletes a memory point. Everything the dream *learns* —
duplicate reports, cluster maps, stale reports, narratives — is written
here, to a separate collection that DREAM owns completely.

Additive and connective, never subtractive. The archive stays untouched;
the journal only grows. Past dreams become searchable memories of their own,
which is the point: a daemon that can look back on what it dreamed.
"""

import time
import uuid


class DreamStore:
    def __init__(self, client, collection, embedder=None, vector_size=384):
        self.client = client
        self.collection = collection
        self.embedder = embedder
        self.vector_size = vector_size
        # Points need vectors; without an embedder the store cannot accept
        # artifacts and DREAM degrades gracefully to report-only.
        self.enabled = embedder is not None
        self.artifacts_written = 0
        self.skipped = 0
        self._collection_ensured = False

    def ensure_collection(self):
        """Create the dream journal collection if it doesn't exist yet."""
        if self._collection_ensured:
            return
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection, size=self.vector_size, distance="Cosine"
            )
        self._collection_ensured = True

    def write_artifact(self, kind, title, text, meta=None):
        """Append one dream artifact to the journal.

        kind:   e.g. 'n1_duplicates', 'n2_clusters', 'n3_stale', 'storyweave'
        title:  short human-readable summary
        text:   the artifact body (gets embedded, so past dreams are searchable)
        meta:   arbitrary structured payload merged in

        Returns the new point id, or None if the store is disabled/failed.
        """
        if self.embedder is None:
            self.skipped += 1
            return None
        try:
            vectors = self.embedder.embed([text])
            if not vectors:
                self.skipped += 1
                return None
            self.ensure_collection()
            point_id = str(uuid.uuid4())
            payload = {
                "kind": kind,
                "title": title,
                "text": text,
                "timestamp": time.time(),
            }
            payload.update(meta or {})
            ok = self.client.upsert_points(self.collection, [{
                "id": point_id,
                "vector": vectors[0],
                "payload": payload,
            }])
            if ok:
                self.artifacts_written += 1
                return point_id
        except Exception:
            # A journal write must never break the dream itself
            self.skipped += 1
        return None

    def status(self):
        return {
            "collection": self.collection,
            "enabled": self.enabled,
            "artifacts_written": self.artifacts_written,
            "skipped": self.skipped,
        }
