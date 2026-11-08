"""N1 — Light consolidation: find exact duplicates.

READ-ONLY toward the archive. N1 finds byte-identical duplicate memories and
reports them; it never deletes. What to *do* about duplicates is a human
decision, made outside the dream. Findings are appended to the dream journal
(see DreamStore) when one is configured.
"""

import hashlib


class N1Consolidation:
    def __init__(self, client, collection, dry_run=False, dream_store=None):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run
        self.dream_store = dream_store

    def _text_hash(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def run(self):
        all_points = []
        offset = None
        while True:
            points, next_offset = self.client.scroll_points(
                self.collection, limit=100, offset=offset, with_payload=True, with_vector=True
            )
            if not points:
                break
            all_points.extend(points)
            offset = next_offset
            if offset is None:
                break

        # Find exact duplicates by text hash
        seen_hashes = {}
        duplicates = []
        duplicate_samples = []
        for p in all_points:
            text = p.get("payload", {}).get("text", "")
            h = self._text_hash(text)
            if h in seen_hashes:
                duplicates.append(p["id"])
                if len(duplicate_samples) < 50:
                    duplicate_samples.append(
                        {"id": p["id"], "kept": seen_hashes[h], "text": text[:120]}
                    )
            else:
                seen_hashes[h] = p["id"]

        # Never delete from the archive. Report only; the human decides.
        result = {
            "phase": "n1",
            "points_reviewed": len(all_points),
            "duplicates_found": len(duplicates),
            "duplicates_removed": 0,  # always 0 — N1 never removes
            "duplicate_samples": duplicate_samples,
            "archive_modified": False,
            "dry_run": self.dry_run,
        }

        if self.dream_store is not None and duplicates:
            artifact_text = "\n".join(
                f"{d['id']} duplicates {d['kept']}: {d['text']}" for d in duplicate_samples
            )
            artifact_id = self.dream_store.write_artifact(
                "n1_duplicates",
                f"{len(duplicates)} exact duplicates found",
                artifact_text,
                {"collection": self.collection},
            )
            result["artifact_id"] = artifact_id

        return result
