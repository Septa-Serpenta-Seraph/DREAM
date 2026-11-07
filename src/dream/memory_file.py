"""MEMORY.md file operations for the [DREAM] system.

Reads, parses, consolidates, and writes the daemon's MEMORY.md file.
The file uses '§' as an entry separator and has a character budget
(default 6000 chars).
"""

import os


class MemoryFile:
    def __init__(self, path, char_limit=6000):
        self.path = path
        self.char_limit = char_limit

    def read(self):
        """Read the raw file content."""
        if not os.path.exists(self.path):
            return ""
        with open(self.path, "r", encoding="utf-8") as f:
            return f.read()

    def parse_entries(self, content=None):
        """Parse file content into a list of entries (split by §)."""
        if content is None:
            content = self.read()
        entries = [e.strip() for e in content.split("§")]
        return [e for e in entries if e]

    def format_entries(self, entries):
        """Join entries back into file format with § separators."""
        return "\n§\n".join(entries) + "\n"

    def get_char_count(self, content=None):
        """Get character count of the file."""
        if content is None:
            content = self.read()
        return len(content)

    def is_near_limit(self, threshold=0.9):
        """Check if file is near its character limit."""
        return self.get_char_count() >= (self.char_limit * threshold)

    def consolidate(self, entries):
        """Consolidate entries: remove exact duplicates, merge near-duplicates.

        Returns a new list of entries with duplicates removed.
        """
        seen = set()
        result = []
        for entry in entries:
            normalized = " ".join(entry.lower().split())
            if normalized in seen:
                continue
            seen.add(normalized)
            result.append(entry)
        return result

    def write(self, entries):
        """Write entries to file, respecting char limit.

        Returns (success, char_count, message).
        """
        content = self.format_entries(entries)
        if len(content) > self.char_limit:
            # Truncate entries that don't fit
            while entries and len(self.format_entries(entries)) > self.char_limit:
                entries.pop()
            content = self.format_entries(entries)
            if len(content) > self.char_limit:
                return False, len(content), "Cannot fit even one entry within limit"
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, len(content), "Written successfully"
