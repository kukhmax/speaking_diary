#!/usr/bin/env python3
"""
Clean project caches and temporary files.
Removes directories like __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, .tox, .hypothesis
and files like *.pyc, *.pyo, .coverage.

Usage:
  python scripts/clean_cache.py [--root PATH] [--dry-run]

Options:
  --root PATH   Root directory to clean (default: current working directory).
  --dry-run     Print what would be removed without deleting.

Notes:
- This script DOES NOT remove the virtual environment (.venv).
- Safe to run multiple times.
"""

from __future__ import annotations
import argparse
import os
import sys
import shutil
from pathlib import Path

DIR_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".hypothesis",
]

FILE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    ".coverage",
]

EXCLUDE_DIRS = {".venv", ".git"}


def remove_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] rmdir {path}")
        return
    try:
        shutil.rmtree(path)
        print(f"[ok] rmdir {path}")
    except Exception as e:
        print(f"[err] rmdir {path}: {e}")


def remove_file(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] rm {path}")
        return
    try:
        path.unlink(missing_ok=True)
        print(f"[ok] rm {path}")
    except Exception as e:
        print(f"[err] rm {path}: {e}")


def should_skip(path: Path) -> bool:
    # Skip excluded directories anywhere in path
    parts = set(path.parts)
    return any(ex in parts for ex in EXCLUDE_DIRS)


def clean(root: Path, dry_run: bool) -> None:
    print(f"Cleaning caches under: {root}")

    # Remove cache directories
    for dir_name in DIR_PATTERNS:
        for p in root.rglob(dir_name):
            if p.is_dir() and not should_skip(p):
                remove_dir(p, dry_run)

    # Remove cache files
    for pattern in FILE_PATTERNS:
        for p in root.rglob(pattern):
            if p.is_file() and not should_skip(p):
                remove_file(p, dry_run)

    print("Done.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean project caches")
    parser.add_argument("--root", default=os.getcwd(), help="Root directory to clean")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    root = Path(args.root).resolve()
    clean(root, dry_run=args.dry_run)