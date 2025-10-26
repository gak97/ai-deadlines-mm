#!/usr/bin/env python3
"""Consolidate conference data from multiple sources.

This script orchestrates the existing helpers in ``.github/scripts`` to
collect AI conference information from both the ``ccfddl`` repository
and the Gemini-backed discovery scraper.  The resulting conference list is
written to ``_data/conferences.yml`` (creating the directory if it does not
already exist).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import yaml

# Ensure we can import the helper scripts that live under .github/scripts
ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / ".github" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import the existing helper modules after adjusting the path
import update_conferences  # type: ignore  # noqa: E402
from ai_conference_discovery import (  # type: ignore  # noqa: E402
    ConferenceCandidate,
    ConferenceDiscoveryEngine,
)

# Paths we care about.  The consolidated output is always written to _data,
# but we read the input from whichever location currently exists so that the
# script behaves correctly both locally and in CI.
PRIMARY_DATA_PATH = ROOT / "src" / "data" / "conferences.yml"
LEGACY_DATA_PATH = ROOT / "_data" / "conferences.yml"
TARGET_DATA_PATH = LEGACY_DATA_PATH


def load_existing_conferences(paths: Sequence[Path]) -> List[Dict[str, Any]]:
    """Load the first conferences.yml file that exists in ``paths``."""

    for path in paths:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                existing = yaml.safe_load(handle) or []
            print(f"📂 Loaded {len(existing)} existing conferences from {path}")
            return existing
    return []


def fetch_ccf_conferences() -> List[Dict[str, Any]]:
    """Fetch and transform conference entries from the CCF repository."""

    try:
        raw_items = update_conferences.fetch_conference_files()
        transformed = update_conferences.transform_conference_data(raw_items)
        print(f"🌐 Retrieved {len(transformed)} conferences from ccfddl")
        return transformed
    except Exception as exc:  # pragma: no cover - network failures
        print(f"⚠️  Failed to fetch CCF conference data: {exc}")
        return []


def candidate_to_entry(
    engine: ConferenceDiscoveryEngine, candidate: ConferenceCandidate
) -> Dict[str, Any]:
    """Convert an ``ConferenceCandidate`` into the YAML entry format."""

    # Use the discovered year when available, otherwise assume the next
    # conference edition will happen in the upcoming year.
    year = candidate.year or datetime.now().year + 1
    entry: Dict[str, Any] = {
        "title": candidate.title,
        "year": year,
        "id": engine._generate_conference_id(candidate.title, year),
        "full_name": candidate.full_name or candidate.title,
        "link": candidate.url,
        "deadline": engine._parse_deadline(candidate.deadline),
        "timezone": "AoE",
        "date": candidate.conference_date,
        "tags": candidate.tags,
        "city": candidate.city,
        "country": candidate.country,
        "note": f"Auto-discovered from {candidate.source}. Please verify details.",
    }
    if candidate.abstract_deadline:
        entry["abstract_deadline"] = engine._parse_deadline(
            candidate.abstract_deadline
        )
    return entry


def fetch_discovered_conferences() -> List[Dict[str, Any]]:
    """Run the discovery engine and convert candidates into entries."""

    engine = ConferenceDiscoveryEngine()
    candidates = engine.discover_conferences()
    entries = [candidate_to_entry(engine, cand) for cand in candidates]
    print(f"🤖 Generated {len(entries)} conferences from AI discovery")
    return entries


def merge_conference_lists(
    base: List[Dict[str, Any]], updates: Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge ``updates`` into ``base`` using (title, year) as the key."""

    index: Dict[Tuple[Any, Any], int] = {
        (conf.get("title"), conf.get("year")): i for i, conf in enumerate(base)
    }
    for conf in updates:
        key = (conf.get("title"), conf.get("year"))
        if key in index:
            existing = base[index[key]]
            for field, value in conf.items():
                existing[field] = value
        else:
            base.append(conf)
            index[key] = len(base) - 1
    return base


def sort_conferences(conferences: List[Dict[str, Any]]) -> None:
    """Sort conferences in-place by deadline so the YAML stays tidy."""

    def sort_key(item: Dict[str, Any]) -> str:
        deadline = item.get("deadline") or "9999"
        if isinstance(deadline, str):
            return deadline
        return "9999"

    conferences.sort(key=sort_key)


def save_conferences(path: Path, conferences: List[Dict[str, Any]]) -> None:
    """Write the conferences back to YAML, ensuring the directory exists."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(conferences, handle, default_flow_style=False, sort_keys=False)
    print(f"💾 Saved {len(conferences)} conferences to {path}")


def main() -> None:
    existing = load_existing_conferences([PRIMARY_DATA_PATH, LEGACY_DATA_PATH])

    ccf_entries = fetch_ccf_conferences()
    ai_entries = fetch_discovered_conferences()

    merged = merge_conference_lists(existing, ccf_entries)
    merged = merge_conference_lists(merged, ai_entries)

    sort_conferences(merged)
    save_conferences(TARGET_DATA_PATH, merged)


if __name__ == "__main__":
    main()
