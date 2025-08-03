"""
Update Conferences
==================

This script fetches the latest AI conference data from the
`ccfddl/ccf-deadlines` repository, transforms it into the format used
by this website and merges it into the existing `conferences.yml`
file.  It is inspired by the original script from the Hugging Face
`ai-conference-deadlines` project but has been simplified and adapted
to write directly into either `src/data/conferences.yml` or
`_data/conferences.yml`, depending on which exists.

Usage:

    python .github/scripts/update_conferences.py

This script is intended to be called from a GitHub Action.  It
assumes that the repository has been checked out and that any
dependencies listed in `.github/scripts/requirements.txt` have been
installed.
"""

import yaml
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
import os


def fetch_conference_files() -> List[Dict[str, Any]]:
    """Fetch all conference YAML files from the ccfddl repository.

    The CCF AI deadlines repository stores one YAML file per
    conference under the `conference/AI` folder.  Each file contains a
    list with a single dictionary that holds metadata for all
    instances of that conference.
    """
    api_url = "https://api.github.com/repos/ccfddl/ccf-deadlines/contents/conference/AI"
    response = requests.get(api_url)
    response.raise_for_status()
    files = response.json()
    conferences: List[Dict[str, Any]] = []
    for file in files:
        if file.get("name", "").endswith(".yml"):
            yaml_content = requests.get(file["download_url"]).text
            conf_data = yaml.safe_load(yaml_content)
            if isinstance(conf_data, list) and conf_data:
                conferences.append(conf_data[0])
    return conferences


def parse_date_range(date_str: str, year: str) -> Tuple[str, str]:
    """Parse a date range string (e.g. "May 29 - Jun 3") into ISO dates.

    Returns a tuple (start_date, end_date) in YYYY-MM-DD format.  If the
    range cannot be parsed a ValueError is raised.
    """
    # Remove the year suffix from the date string, e.g. "April 24-28, 2025"
    date_str = date_str.replace(f", {year}", "")
    # Split into start and end parts
    if " - " in date_str:
        start, end = date_str.split(" - ")
    elif "-" in date_str:
        start, end = date_str.split("-")
    else:
        start = end = date_str

    # Normalise month abbreviations to full names
    month_map = {
        "Sept": "September",
        "Jan": "January",
        "Feb": "February",
        "Mar": "March",
        "Apr": "April",
        "Jun": "June",
        "Jul": "July",
        "Aug": "August",
        "Sep": "September",
        "Oct": "October",
        "Nov": "November",
        "Dec": "December",
    }

    # If the end part doesn't contain a month, copy the month from the start
    all_months = set(month_map.keys()) | set(month_map.values())
    if not any(month in end for month in all_months):
        start_parts = start.strip().split()
        if start_parts:
            end = f"{start_parts[0]} {end.strip()}"

    # Replace abbreviations
    for abbr, full in month_map.items():
        start = start.replace(abbr, full)
        end = end.replace(abbr, full)

    start = " ".join(start.strip().split())
    end = " ".join(end.strip().split())

    start_dt = datetime.strptime(f"{start}, {year}", "%B %d, %Y")
    end_dt = datetime.strptime(f"{end}, {year}", "%B %d, %Y")
    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")


def transform_conference_data(conferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform the CCF format into our internal format.

    The CCF format nests multiple instances of a conference under the key
    ``confs``.  We pick the first instance that is in the current or
    future year and map the fields into the structure expected by
    `conferences.yml`.
    """
    transformed: List[Dict[str, Any]] = []
    current_year = datetime.now().year

    for conf in conferences:
        # Find the most recent or upcoming instance
        recent_instance = None
        for inst in conf.get("confs", []):
            if inst.get("year", 0) >= current_year:
                recent_instance = inst
                break
        if not recent_instance:
            continue

        # Build our conference entry
        entry: Dict[str, Any] = {
            "title": conf.get("title", ""),
            "year": recent_instance.get("year"),
            "id": recent_instance.get("id"),
            "full_name": conf.get("description", ""),
            "link": recent_instance.get("link", ""),
            "deadline": recent_instance.get("timeline", [{}])[0].get("deadline", ""),
            "timezone": recent_instance.get("timezone", ""),
            "date": recent_instance.get("date", ""),
            "tags": [],  # categories not provided by CCF
        }

        # Parse city and country from the 'place' field
        place = recent_instance.get("place", "")
        if place:
            if "," in place:
                city, country = place.split(",", 1)
                entry["city"] = city.strip()
                entry["country"] = country.strip()
            else:
                entry["country"] = place.strip()

        # Abstract deadline
        timeline = recent_instance.get("timeline", [{}])[0]
        if "abstract_deadline" in timeline:
            entry["abstract_deadline"] = timeline["abstract_deadline"]

        # Convert the date range into explicit start/end values
        if entry["date"]:
            try:
                start, end = parse_date_range(entry["date"], str(entry["year"]))
                entry["start"] = start
                entry["end"] = end
            except Exception as e:
                print(f"Warning: Could not parse date '{entry['date']}' for {entry['title']}: {e}")

        # Handle rankings if present
        rank_info = conf.get("rank", {})
        if rank_info:
            rankings: List[str] = []
            for rank_type, rank_value in rank_info.items():
                rankings.append(f"{rank_type.upper()}: {rank_value}")
            if rankings:
                entry["rankings"] = ", ".join(rankings)

        transformed.append(entry)

    return transformed


def load_existing_conferences(path: str) -> List[Dict[str, Any]]:
    """Load the existing conferences from the given YAML path."""
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return yaml.safe_load(f) or []


def save_conferences(path: str, conferences: List[Dict[str, Any]]) -> None:
    """Save the conference list back to YAML, sorting by deadline."""
    # Normalise deadlines so that missing or invalid values sort to the end
    def sort_key(item: Dict[str, Any]) -> str:
        return item.get("deadline", "9999") or "9999"
    conferences.sort(key=sort_key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(conferences, f, default_flow_style=False, sort_keys=False)


def main() -> None:
    # Determine the path of the conference file.  Prefer src/data over _data.
    primary_path = os.path.join("src", "data", "conferences.yml")
    fallback_path = os.path.join("_data", "conferences.yml")
    target_path = primary_path if os.path.exists(primary_path) else fallback_path

    current_confs = load_existing_conferences(target_path)
    # Build an index of existing conferences by (title, year)
    existing_index = {(c.get("title"), c.get("year")): i for i, c in enumerate(current_confs)}

    try:
        raw_confs = fetch_conference_files()
    except Exception as e:
        print(f"Error fetching data from ccfddl: {e}")
        return
    transformed = transform_conference_data(raw_confs)
    if not transformed:
        print("No new conferences fetched from ccfddl.")
        return

    # Merge new conferences into the existing list.  Update entries if they
    # already exist, otherwise append them.
    for conf in transformed:
        key = (conf.get("title"), conf.get("year"))
        if key in existing_index:
            # Update existing entry while preserving any local fields such as notes
            idx = existing_index[key]
            for field, value in conf.items():
                current_confs[idx][field] = value
        else:
            current_confs.append(conf)
            existing_index[key] = len(current_confs) - 1

    save_conferences(target_path, current_confs)
    print(f"Updated conferences file with {len(transformed)} entries from ccfddl.")


if __name__ == "__main__":
    main()
