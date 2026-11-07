"""REM — Integration: cross-memory synthesis, immune system checks."""

from datetime import datetime, timezone


class N4REM:
    def __init__(self, client, collection, dry_run=False):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run

    def run(self):
        all_points = []
        offset = None
        while True:
            points, next_offset = self.client.scroll_points(
                self.collection, limit=100, offset=offset, with_payload=True, with_vector=False
            )
            if not points:
                break
            all_points.extend(points)
            offset = next_offset
            if offset is None:
                break

        # Count by role
        role_counts = {}
        for p in all_points:
            role = p.get("payload", {}).get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        # Immune system checks
        point_count = self.client.get_point_count(self.collection)
        immune = {
            "point_count": point_count,
            "point_count_healthy": point_count > 0,
            "role_distribution": role_counts,
        }

        summary = (
            f"REM integration complete. Reviewed {len(all_points)} memories. "
            f"Role distribution: {role_counts}. "
            f"Collection has {point_count} total points."
        )

        return {
            "phase": "rem",
            "points_reviewed": len(all_points),
            "role_distribution": role_counts,
            "immune_checks": immune,
            "summary": summary,
            "dry_run": self.dry_run,
        }
