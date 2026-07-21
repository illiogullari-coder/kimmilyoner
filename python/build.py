"""Build entry point for the question generation pipeline."""
from __future__ import annotations

import sys

from generate_questions import main

if __name__ == "__main__":
    sys.exit(main())
