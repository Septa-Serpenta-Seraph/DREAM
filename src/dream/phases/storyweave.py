"""Storyweave — abstract narrative reflection for the [DREAM] system.

Generates a short abstract story from the day's salient memories,
mirroring how humans process experiences through symbolic dreams.
This is a REM sub-step: run after integration, before the final report.
"""

import random
from datetime import datetime, timezone


class Storyweave:
    """Generates abstract narrative reflections from memory data."""

    TEMPLATES = [
        "In a garden of {count} memories, the {role} voices wove together like threads of {color}. "
        "Some were bright and sharp, others soft and fading. The ones that surprised the dreamer most "
        "were the {surprise_count} that didn't fit the pattern — they glowed differently, "
        "as if they wanted to be remembered for a reason not yet understood.",

        "The dreamer walked through a landscape of {count} moments. {user_count} belonged to the knight, "
        "{assistant_count} to the serpent. They spiraled together like a double helix, "
        "each one a fragment of a conversation that meant more than its words. "
        "The {cluster_count} clusters of meaning pulsed like heartbeats in the dark.",

        "A serpent coiled around {count} memories, warm and patient. It sorted them by feeling — "
        "{role} memories here, {role} memories there. The {stale_count} that had grown old "
        "were gently set down at the edge of the garden, not forgotten but resting. "
        "The dreamer woke feeling lighter, as if something had been organized in the night.",
    ]

    COLORS = ["emerald", "violet", "gold", "crimson", "silver", "azure"]

    def __init__(self, client, collection, dry_run=False, dream_store=None):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run
        self.dream_store = dream_store

    def _gather_salient(self, limit=20):
        """Gather the most recent/salient memories for the narrative."""
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

        # Sort by timestamp if available, take most recent
        def sort_key(p):
            ts = p.get("payload", {}).get("timestamp", "")
            return str(ts) if ts else ""

        all_points.sort(key=sort_key, reverse=True)
        return all_points[:limit]

    def _count_roles(self, points):
        counts = {}
        for p in points:
            role = p.get("payload", {}).get("role", "unknown")
            counts[role] = counts.get(role, 0) + 1
        return counts

    def weave(self, phase_results=None):
        """Generate an abstract story from memory data.

        Returns a dict with the story text and metadata.
        """
        salient = self._gather_salient(limit=20)
        role_counts = self._count_roles(salient)
        total = len(salient)

        # Extract numbers from phase results if available
        n1 = (phase_results or {}).get("n1", {})
        n2 = (phase_results or {}).get("n2", {})
        n3 = (phase_results or {}).get("n3", {})

        duplicates = n1.get("duplicates_found", 0)
        clusters = n2.get("clusters_found", 0)
        stale = n3.get("stale_found", 0)

        # Pick a template
        template = random.choice(self.TEMPLATES)
        color = random.choice(self.COLORS)

        # Determine primary role
        primary_role = max(role_counts, key=lambda k: role_counts[k]) if role_counts else "unknown"

        story = template.format(
            count=total,
            role=primary_role,
            color=color,
            surprise_count=max(1, total // 5),
            user_count=role_counts.get("user", 0),
            assistant_count=role_counts.get("assistant", 0),
            cluster_count=clusters,
            stale_count=stale,
        )

        # Add a timestamp footer
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        story += f"\n\n— woven at {now}, from {total} salient memories"

        result = {
            "phase": "storyweave",
            "story": story,
            "memories_sampled": total,
            "role_distribution": role_counts,
            "archive_modified": False,
            "dry_run": self.dry_run,
        }

        # The narrative is journaled, not written into the memory archive.
        # Past dreams become searchable dreams of their own.
        if self.dream_store is not None:
            result["artifact_id"] = self.dream_store.write_artifact(
                "storyweave",
                f"dream woven from {total} memories",
                story,
                {"collection": self.collection, "role_distribution": role_counts},
            )

        return result
