"""N2 — Spindle: connect new memories to existing ones, find patterns."""

import math


class N2Spindle:
    def __init__(self, client, collection, dry_run=False, similarity_threshold=0.85):
        self.client = client
        self.collection = collection
        self.dry_run = dry_run
        self.threshold = similarity_threshold

    def _cosine_similarity(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

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

        # Update payloads with cluster info (if not dry run)
        if not self.dry_run:
            for ci, cluster in enumerate(clusters):
                for p in cluster:
                    payload = dict(p.get("payload", {}) or {})
                    payload["cluster_id"] = ci
                    payload["cluster_size"] = len(cluster)
                    payload["cluster_members"] = [m["id"] for m in cluster]
                    self.client.upsert_points(self.collection, [{
                        "id": p["id"],
                        "vector": p.get("vector", []),
                        "payload": payload,
                    }])

        return {
            "phase": "n2",
            "points_reviewed": len(all_points),
            "clusters_found": len(clusters),
            "clustered_points": sum(len(c) for c in clusters),
            "dry_run": self.dry_run,
        }