"""N3 — Deep pruning: remove stale memories, correct drift, optimize."""

from datetime import datetime, timezone, timedelta


class N3Pruning:
    def __init__(self, client, collection, max_age_days=90, dry_run=False):
        self.client = client
        self.collection = collection
        self.max_age_days = max_age_days
        self.dry_run = dry_run

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
        for p in all_points:
            ts = self._parse_timestamp(p.get("payload", {}).get("timestamp"))
            if ts and ts < cutoff:
                stale_ids.append(p["id"])

        if not self.dry_run and stale_ids:
            self.client.delete_points(self.collection, stale_ids)

        return {
            "phase": "n3",
            "points_reviewed": len(all_points),
            "stale_found": len(stale_ids),
            "stale_removed": len(stale_ids) if not self.dry_run else 0,
            "dry_run": self.dry_run,
        }
