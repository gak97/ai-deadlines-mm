#!/usr/bin/env python3
"""Legacy wrapper to regenerate conference and index pages from YAML data."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.generate_pages import main


if __name__ == "__main__":
    main()
