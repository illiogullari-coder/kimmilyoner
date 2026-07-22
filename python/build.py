"""Build entry point for the question generation pipeline.

Usage:
    python python/build.py

Must be run from the repository root (or any directory — Path resolution is
relative to this file's location, not cwd).
"""
from __future__ import annotations

import os
import sys

# Ensure the python/ directory is on the path so sibling modules resolve
sys.path.insert(0, os.path.dirname(__file__))

from generate_questions import main

if __name__ == "__main__":
    sys.exit(main())
