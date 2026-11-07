# tests/test_memory_file.py
import os
import tempfile
import pytest
from dream.memory_file import MemoryFile


def test_memory_file_read():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("entry one\n§\nentry two\n")
        path = f.name
    try:
        mf = MemoryFile(path)
        content = mf.read()
        assert "entry one" in content
        assert "entry two" in content
    finally:
        os.unlink(path)


def test_memory_file_parse_entries():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("entry one\n§\nentry two\n§\nentry three\n")
        path = f.name
    try:
        mf = MemoryFile(path)
        entries = mf.parse_entries()
        assert len(entries) == 3
        assert entries[0] == "entry one"
        assert entries[1] == "entry two"
        assert entries[2] == "entry three"
    finally:
        os.unlink(path)


def test_memory_file_consolidate_removes_duplicates():
    mf = MemoryFile("/tmp/nonexistent.md")
    entries = ["hello world", "hello world", "different entry"]
    consolidated = mf.consolidate(entries)
    assert len(consolidated) == 2


def test_memory_file_write_respects_limit():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = f.name
    try:
        mf = MemoryFile(path, char_limit=50)
        entries = ["short entry", "another short entry"]
        success, count, msg = mf.write(entries)
        assert success is True
        assert count <= 50
    finally:
        os.unlink(path)


def test_memory_file_near_limit():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("a" * 55)
        path = f.name
    try:
        mf = MemoryFile(path, char_limit=60)
        assert mf.is_near_limit(threshold=0.9) is True
    finally:
        os.unlink(path)
