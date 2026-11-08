"""DreamEngine orchestrator for the DREAM system."""

from dream.qdrant_client import QdrantClient
from dream.dream_store import DreamStore
from dream.phases.n1_consolidation import N1Consolidation
from dream.phases.n2_spindle import N2Spindle
from dream.phases.n3_pruning import N3Pruning
from dream.phases.n4_rem import N4REM
from dream.phases.storyweave import Storyweave
from dream.memory_file import MemoryFile

try:
    from dream.embedder import FastEmbedEmbedder
except Exception:  # pragma: no cover
    FastEmbedEmbedder = None


PHASE_ORDER = ["n1", "n2", "n3", "rem", "storyweave"]


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
        memory_file_path=None,
        dream_collection=None,
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
        self.memory_file_path = memory_file_path
        self.memory_file = MemoryFile(memory_file_path) if memory_file_path else None

        self.fastembed_python = fastembed_python
        self.fastembed_script = fastembed_script
        self.embedder = None
        if fastembed_python and fastembed_script and FastEmbedEmbedder is not None:
            self.embedder = FastEmbedEmbedder(fastembed_python, fastembed_script)

        # The dream journal: the ONLY collection DREAM writes to.
        # The memory archive is read-only to every phase.
        self.dream_store = None
        if dream_collection:
            self.dream_store = DreamStore(self.client, dream_collection, self.embedder)

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
            if name in ("n4",):
                name = "rem"
            if name in ("sw", "story"):
                name = "storyweave"
            if name in ("mf", "memory-file", "memoryfile"):
                name = "memoryfile"
            if name in PHASE_ORDER or name == "memoryfile":
                out.append(name)
        if not out:
            out = list(PHASE_ORDER)
        return out

    def _run_phase(self, name):
        if name == "n1":
            phase = N1Consolidation(self.client, self.collection, dry_run=self.dry_run,
                                    dream_store=self.dream_store)
            return phase.run()
        elif name == "n2":
            phase = N2Spindle(
                self.client, self.collection, dry_run=self.dry_run,
                similarity_threshold=self.similarity_threshold,
                dream_store=self.dream_store,
            )
            return phase.run()
        elif name == "n3":
            phase = N3Pruning(
                self.client, self.collection, max_age_days=self.max_age_days,
                dry_run=self.dry_run,
                dream_store=self.dream_store,
            )
            return phase.run()
        elif name == "rem":
            phase = N4REM(self.client, self.collection, dry_run=self.dry_run)
            return phase.run()
        elif name == "storyweave":
            phase = Storyweave(self.client, self.collection, dry_run=self.dry_run,
                               dream_store=self.dream_store)
            phase_results = getattr(self, "_current_phase_results", {})
            return phase.weave(phase_results)
        elif name == "memoryfile":
            return self._run_memoryfile_phase()
        else:
            raise ValueError(f"Unknown phase: {name}")

    def _run_memoryfile_phase(self):
        """Consolidate MEMORY.md entries."""
        if self.memory_file is None:
            return {"phase": "memoryfile", "status": "skipped", "reason": "no memory file path configured"}
        entries = self.memory_file.parse_entries()
        original_count = len(entries)
        consolidated = self.memory_file.consolidate(entries)
        removed = original_count - len(consolidated)
        if not self.dry_run:
            self.memory_file.write(consolidated)
        return {
            "phase": "memoryfile",
            "entries_before": original_count,
            "entries_after": len(consolidated),
            "duplicates_removed": removed,
            "char_count": self.memory_file.get_char_count(),
            "dry_run": self.dry_run,
        }

    def dream(self, phases=None):
        phase_names = self._normalize_phases(phases)
        report = {
            "collection": self.collection,
            "dry_run": self.dry_run,
            "archive_modified": False,
            "phases_run": [],
            "phases": {},
            "results": [],
        }
        report["phase_results"] = report["results"]
        report["phase_reports"] = report["results"]

        phase_results = {}
        for name in phase_names:
            if name == "storyweave":
                self._current_phase_results = phase_results
            result = self._run_phase(name)
            phase_results[name] = result
            report["phases_run"].append(name)
            report["phases"][name] = result
            report["results"].append(result)
            report[name] = result

        # Journal status is captured AFTER all phases run (a pre-loop snapshot
        # would always report zero artifacts — caught by the engine test)
        if self.dream_store is not None:
            report["dream_store"] = self.dream_store.status()

        return report

    def close(self):
        if self.embedder is not None:
            try:
                self.embedder.close()
            except Exception:
                pass
