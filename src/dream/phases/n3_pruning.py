"""N3 — Deep pruning: remove stale memories, correct drift, optimize."""

from datetime import datetime, timezone, timedelta


class N3Pruning:
    def __init__(self, client, collection, max_age_days=90, dry_run=False, dream_store=None):
        self.client = client
        self.collection = collection
        self.max_age_days = max_age_days
        self.dry_run = dry_run
        self.dream_store = dream_store

    def _parse_timestamp(self, ts):
        if not ts:
            return None
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

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

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        stale_ids = []
        stale_entries = []
        for p in all_points:
            ts = self._parse_timestamp(p.get("payload", {}).get("timestamp"))
            if ts and ts < cutoff:
                stale_ids.append(p["id"])
                stale_entries.append({
                    "id": p["id"],
                    "text": (p.get("payload", {}).get("text", "") or "")[:100],
                    "timestamp": p.get("payload", {}).get("timestamp"),
                })

        # REPORT ONLY — never modify, never archive, never delete
        # The human decides what to do with stale memories
        result = {
            "phase": "n3",
            "points_reviewed": len(all_points),
            "stale_found": len(stale_ids),
            "stale_entries": stale_entries,
            "stale_archived": 0,  # Never archive — report only
            "stale_removed": 0,  # Never remove — report only
            "dry_run": True,  # Always report-only
            "archive_modified": False,
            "note": "N3 is report-only. No modifications made. Human decides.",
        }

        if self.dream_store is not None and stale_entries:
            artifact_text = "\n".join(
                f"{e['id']} (last seen {e['timestamp']}): {e['text']}"
                for e in stale_entries[:50]
            )
            result["artifact_id"] = self.dream_store.write_artifact(
                "n3_stale",
                f"{len(stale_ids)} stale memories reported",
                artifact_text,
                {"collection": self.collection},
            )

        return result
