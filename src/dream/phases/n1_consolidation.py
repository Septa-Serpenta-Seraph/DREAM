"""N1 — Light consolidation: deduplicate, reorganize, update timestamps."""

import hashlib


class N1Consolidation:
    def __init__(self, client, collection, dry_run=False):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run

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
        for p in all_points:
            text = p.get("payload", {}).get("text", "")
            h = self._text_hash(text)
            if h in seen_hashes:
                duplicates.append(p["id"])
            else:
                seen_hashes[h] = p["id"]

        if not self.dry_run and duplicates:
            self.client.delete_points(self.collection, duplicates)

        return {
            "phase": "n1",
            "points_reviewed": len(all_points),
            "duplicates_found": len(duplicates),
            "duplicates_removed": len(duplicates) if not self.dry_run else 0,
            "dry_run": self.dry_run,
        }
