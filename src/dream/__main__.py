"""CLI entry point for the DREAM system."""

import argparse
import json
import sys
from dream.engine import DreamEngine


def main():
    parser = argparse.ArgumentParser(description="DREAM — Daemon Memory Reorganization Engine")
    parser.add_argument("--qdrant-url", default="http://localhost:6333", help="Qdrant REST API URL")
    parser.add_argument("--collection", required=True, help="Qdrant collection name to dream about")
    parser.add_argument("--phases", nargs="+", default=["n1", "n2", "n3", "rem"],
                        choices=["n1", "n2", "n3", "rem", "storyweave", "memoryfile", "all"],
                        help="Which phases to run (default: all)")
    parser.add_argument("--fastembed-python", default="/mnt/data/fe-venv/bin/python",
                        help="Path to Python with fastembed installed")
    parser.add_argument("--fastembed-script", default="/home/adora/.hermes/scripts/embed_fastembed_local.py",
                        help="Path to fastembed daemon script")
    parser.add_argument("--report-file", default=None, help="Path to write JSON report")
    parser.add_argument("--memory-file", default=None, help="Path to MEMORY.md file for consolidation")
    parser.add_argument("--dry-run", action="store_true", help="Report only, don't modify")
    args = parser.parse_args()

    if "all" in args.phases:
        args.phases = ["n1", "n2", "n3", "rem", "storyweave"]
        if args.memory_file:
            args.phases.append("memoryfile")

    engine = DreamEngine(
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        fastembed_python=args.fastembed_python,
        fastembed_script=args.fastembed_script,
        memory_file_path=args.memory_file,
        dry_run=args.dry_run,
    )

    report = engine.dream(phases=args.phases)

    if args.report_file:
        with open(args.report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.report_file}")
    else:
        print(json.dumps(report, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()