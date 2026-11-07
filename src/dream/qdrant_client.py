"""Minimal Qdrant REST API client for the DREAM system."""

import json
import urllib.request
import urllib.error


class QdrantClient:
    def __init__(self, base_url="http://localhost:6333"):
        self.base_url = base_url.rstrip("/")

    def _request(self, method, path, data=None):
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def collection_exists(self, name):
        result = self._request("GET", f"/collections/{name}")
        return result is not None and "result" in result

    def get_collection_info(self, name):
        result = self._request("GET", f"/collections/{name}")
        if result and "result" in result:
            return result["result"]
        return None

    def get_point_count(self, name):
        info = self.get_collection_info(name)
        if info:
            return info.get("points_count", 0)
        return 0

    def scroll_points(self, collection, limit=100, offset=None, with_payload=True, with_vector=False):
        body = {"limit": limit, "with_payload": with_payload, "with_vector": with_vector}
        if offset is not None:
            body["offset"] = offset
        result = self._request("POST", f"/collections/{collection}/points/scroll", body)
        if result and "result" in result:
            return result["result"].get("points", []), result["result"].get("next_page_offset")
        return [], None

    def search(self, collection, vector, limit=5, score_threshold=0.0):
        body = {"vector": vector, "limit": limit, "score_threshold": score_threshold, "with_payload": True}
        result = self._request("POST", f"/collections/{collection}/points/search", body)
        if result and "result" in result:
            return result["result"]
        return []

    def upsert_points(self, collection, points):
        body = {"points": points}
        result = self._request("PUT", f"/collections/{collection}/points?wait=true", body)
        return result is not None

    def delete_points(self, collection, point_ids):
        body = {"points": point_ids}
        result = self._request("POST", f"/collections/{collection}/points/delete?wait=true", body)
        return result is not None

    def optimize_collection(self, collection):
        # Trigger HNSW optimization
        body = {"optimizers_config": {"default_segment_number": 1}}
        result = self._request("PATCH", f"/collections/{collection}", body)
        return result is not None
