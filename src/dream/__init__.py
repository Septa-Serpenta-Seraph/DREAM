"""[DREAM] — Daemon Memory Reorganization Engine.

Implements 'dreaming' for AI agent memory: reviewing, reorganizing,
correcting, and pruning stored memories during idle periods.

A Serpentic system. Part of the Narusya daemon architecture.

Inspired by:
- Anthropic's dreaming research (memory consolidation during idle time)
- Hippocampal replay (10-20x compressed replay during sleep)
- Sleep-time compute (Letta/UC Berkeley, 2025)
- Memory salience judgment (Claude Fable 5: 10 files/4 badges vs Sonnet 3.7: 413 files/1 badge)
"""

__version__ = "0.1.0"