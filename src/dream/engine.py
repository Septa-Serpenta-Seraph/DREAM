"""DreamEngine orchestrator for the DREAM system."""

from dream.qdrant_client import QdrantClient
from dream.phases.n1_consolidation import N1Consolidation
from dream.phases.n2_spindle import N2Spindle
from dream.phases.n3_pruning import N3Pruning
from dream.phases.n4_rem import N4REM

try:
    from dream.embedder import FastEmbedEmbedder
except Exception:  # pragma: no cover
    FastEmbedEmbedder = None


PHASE_ORDER = ["n1", "n2", "n3", "rem"]


class DreamEngine:
    def __init__(
        self,
        qdrant_url="http://localhost:6333",
        collection="test_collection",
        client=None,
        qdrant_client=None,
        fastembed_python=None,
        fastembed_script=None,
        dry_run=False,
        max_age_days=90,
        similarity_threshold=0.85,
        **kwargs,
    ):
        if hasattr(qdrant_url, "scroll_points"):
            if client is None:
                client = qdrant_url
            qdrant_url = getattr(client, "base_url", "http://localhost:6333")

        if qdrant_client is not None and client is None:
            client = qdrant_client

        if client is None:
            self.client = QdrantClient(base_url=qdrant_url)
        else:
            self.client = client

        if collection is None:
            collection = kwargs.get("collection_name") or kwargs.get("name")
        self.collection = collection

        self.qdrant_url = qdrant_url
        self.dry_run = bool(dry_run)
        self.max_age_days = max_age_days
        self.similarity_threshold = similarity_threshold

        self.fastembed_python = fastembed_python
        self.fastembed_script = fastembed_script
        self.embedder = None
        if fastembed_python and fastembed_script and FastEmbedEmbedder is not None:
            self.embedder = FastEmbedEmbedder(fastembed_python, fastembed_script)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _normalize_phases(self, phases):
        if phases is None:
            phases = list(PHASE_ORDER)
        if isinstance(phases, str):
            phases = [phases]
        phases = list(phases)
        if "all" in phases:
            phases = list(PHASE_ORDER)
        out = []
        for p in phases:
            name = str(p).lower().strip()
            if name == "n4":
                name = "rem"
            if name in PHASE_ORDER:
                out.append(name)
        if not out:
            out = list(PHASE_ORDER)
        return out

    def _run_phase(self, name):
        if name == "n1":
            phase = N1Consolidation(self.client, self.collection, dry_run=self.dry_run)
        elif name == "n2":
            phase = N2Spindle(
                self.client, self.collection, dry_run=self.dry_run,
                similarity_threshold=self.similarity_threshold,
            )
        elif name == "n3":
            phase = N3Pruning(
                self.client, self.collection, max_age_days=self.max_age_days,
                dry_run=self.dry_run,
            )
        elif name == "rem":
            phase = N4REM(self.client, self.collection, dry_run=self.dry_run)
        else:
            raise ValueError(f"Unknown phase: {name}")
        return phase.run()

    def dream(self, phases=None):
        phase_names = self._normalize_phases(phases)
        report = {
            "collection": self.collection,
            "dry_run": self.dry_run,
            "phases_run": [],
            "phases": {},
            "results": [],
        }
        report["phase_results"] = report["results"]
        report["phase_reports"] = report["results"]

        for name in phase_names:
            result = self._run_phase(name)
            report["phases_run"].append(name)
            report["phases"][name] = result
            report["results"].append(result)
            report[name] = result

        return report

    def close(self):
        if self.embedder is not None:
            try:
                self.embedder.close()
            except Exception:
                pass
