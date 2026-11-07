# DREAM — Daemon Memory Reorganization Engine

Implements "dreaming" for AI agent memory: reviewing, reorganizing, correcting,
and pruning stored memories during idle periods.

## Research basis

- Anthropic: "Components of agent memory" (2026)
- Anthropic: "Can Claude dream now?" (2026) — quality over quantity
- Letta/UC Berkeley: "Sleep-time Compute" (2025)
- TypeGraph: "Memory Consolidation: How Sleep Inspired Background Memory Agents" (2026)
- Neuroscience News: "AI Emulates Brain's Memory Replay" (2023)
- Wikipedia: "Hippocampal replay"
- Frontiers: "AI insights into hippocampal processing" (2022)
- AWS: "AgentCore long-term memory deep dive" (2025)
- hidekazu-konishi: "AI Agent Memory Design Guide" (2026)
- Redis: "Long-Term Memory Architectures for AI Agents" (2026)

## Usage

```bash
pip install -e .
dream --collection narusya_memories_fastembed --phases all
```

## Phases

- **N1 — Light consolidation**: Deduplicate, reorganize recent memories, update timestamps
- **N2 — Spindle**: Connect new memories to existing ones, find patterns, cross-reference
- **N3 — Deep pruning**: Remove redundant memories, correct drift, optimize storage
- **REM — Integration**: Cross-memory synthesis, lorebook updates, immune system checks