"""N2 — Spindle: find clusters of related memories.

READ-ONLY toward the archive. N2 discovers clusters of similar memories using
Qdrant's search API (not O(n²) pairwise comparison). It never tags, modifies,
or writes back to the memory collection — cluster maps are appended to the
dream journal (see DreamStore) where they are searchable alongside the
memories they describe.
"""


class N2Spindle:
    def __init__(self, client, collection, dry_run=False, similarity_threshold=0.85,
                 dream_store=None):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run
        self.threshold = similarity_threshold
        self.dream_store = dream_store

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

        # Use Qdrant search API for nearest-neighbor clustering (much faster than O(n²))
        id_to_point = {p["id"]: p for p in all_points}
        visited = set()
        clusters = []

        for p1 in all_points:
            if p1["id"] in visited:
                continue
            visited.add(p1["id"])
            vector = p1.get("vector", [])
            if not vector:
                continue

            try:
                neighbors = self.client.search(
                    self.collection, vector, limit=20, score_threshold=self.threshold
                )
            except Exception:
                neighbors = []

            cluster_ids = [p1["id"]]
            for n in neighbors:
                nid = n.get("id")
                if nid is not None and nid != p1["id"] and nid not in visited:
                    cluster_ids.append(nid)
                    visited.add(nid)

            if len(cluster_ids) > 1:
                cluster = [id_to_point[pid] for pid in cluster_ids if pid in id_to_point]
                if len(cluster) > 1:
                    clusters.append(cluster)

        # Never write cluster tags back into the archive. The cluster map
        # lives in the dream journal, additive only.
        result = {
            "phase": "n2",
            "points_reviewed": len(all_points),
            "clusters_found": len(clusters),
            "clustered_points": sum(len(c) for c in clusters),
            "archive_modified": False,
            "dry_run": self.dry_run,
        }

        if self.dream_store is not None and clusters:
            lines = []
            cluster_maps = []
            for ci, cluster in enumerate(clusters[:500]):
                member_ids = [m["id"] for m in cluster]
                sample = (cluster[0].get("payload", {}).get("text", "") or "")[:80]
                lines.append(f"cluster {ci}: {len(cluster)} memories — {sample}")
                cluster_maps.append({"cluster_id": ci, "size": len(cluster),
                                     "members": member_ids})
            artifact_id = self.dream_store.write_artifact(
                "n2_clusters",
                f"{len(clusters)} clusters over {result['clustered_points']} memories",
                "\n".join(lines),
                {"collection": self.collection, "clusters": cluster_maps},
            )
            result["artifact_id"] = artifact_id

        return result
