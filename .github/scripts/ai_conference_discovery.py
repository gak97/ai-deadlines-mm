#!/usr/bin/env python3
"""
AI‑Powered Conference Discovery System (Gemini edition)
=======================================================

This script discovers new AI conferences by scraping a handful of public
sources and then uses a large language model to categorise and validate
those candidates.  It has been adapted from the original Hugging Face
implementation to use Google's Gemini family of models instead of
OpenAI's GPT models.  The primary model used is
``gemini-2.5-flash``.  Authentication is handled via the
``GEMINI_API_KEY`` environment variable which you should set in your
GitHub repository secrets.  If no key is provided the script will
skip the AI enhancement step and simply return scraped candidates.

The script writes new conference entries back into
``src/data/conferences.yml`` (falling back to ``_data/conferences.yml`` if
the ``src/data`` tree does not exist).  New conferences are appended
and the list is sorted by deadline.

Usage:

    pip install -r .github/scripts/requirements.txt
    export GEMINI_API_KEY=...  # optional, enables AI enhancement
    python .github/scripts/ai_conference_discovery.py

"""

import os
import json
import yaml
import time
import requests
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup

try:
    # The Google generative AI SDK is optional; if it's not installed the
    # AI enhancement step will be skipped.  See requirements.txt for
    # installation details.
    import google.generativeai as genai  # type: ignore
except ImportError:
    genai = None


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
# Mapping of our high‑level categories to a list of search keywords used when
# querying WikiCFP.  Additional keywords can be added in
# ``.github/scripts/ai_config.yml`` if desired.  These are kept simple
# compared to the full Hugging Face config for clarity.
TARGET_CATEGORIES: Dict[str, List[str]] = {
    "machine-learning": ["machine learning", "ML", "artificial intelligence", "AI"],
    "computer-vision": ["computer vision", "CV", "image processing"],
    "natural-language-processing": ["natural language processing", "NLP"],
    "robotics": ["robotics", "autonomous systems", "robot"],
    "reinforcement-learning": ["reinforcement learning", "RL"],
    "data-mining": ["data mining", "knowledge discovery"],
    "signal-processing": ["signal processing", "DSP", "audio processing"],
    "human-computer-interaction": ["HCI", "user interface", "UX"],
    "web-search": ["web search", "information retrieval", "search engines"],
    "computer-graphics": ["computer graphics", "visualization"],
    "mathematics": ["mathematics", "numerical methods"],
}


# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------
@dataclass
class ConferenceCandidate:
    """Representation of a potential conference discovered via scraping."""

    title: str
    full_name: str = ""
    url: str = ""
    deadline: str = ""
    abstract_deadline: str = ""
    conference_date: str = ""
    location: str = ""
    city: str = ""
    country: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    year: int = 0
    confidence_score: float = 0.0
    source: str = ""


class ConferenceDiscoveryEngine:
    """Engine that coordinates scraping, AI enhancement and file updates."""

    def __init__(self, gemini_api_key: Optional[str] = None) -> None:
        # The key may be provided directly or read from the environment.  The
        # environment variable ``GEMINI_API_KEY`` should be set in the GitHub
        # repository secrets for production use.  When no key is available the
        # AI step will be skipped.
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def discover_conferences(self) -> List[ConferenceCandidate]:
        """Scrape candidate conferences and optionally enhance them with AI."""
        candidates: List[ConferenceCandidate] = []

        print("🕵️  Starting conference discovery")
        # Only enable scraping sources that are reliable and relatively fast.
        candidates += self._scrape_wikicfp()
        # Additional sources such as deadline trackers could be added here.

        # Use AI to categorise and enrich the scraped candidates.
        enriched = self._ai_enhance_candidates(candidates)
        # Filter the list down to high‑confidence, non‑duplicate entries.
        filtered = self._filter_candidates(enriched)
        print(f"✨ Discovered {len(filtered)} new conference candidates")
        return filtered

    def add_to_conferences_yml(self, candidates: List[ConferenceCandidate]) -> int:
        """Append valid candidates to the conferences YAML file.

        Returns the number of conferences added.
        """
        if not candidates:
            return 0

        # Determine which data file to read/write.  The main site uses
        # ``_data/conferences.yml``, but the Hugging Face scripts expect
        # ``src/data/conferences.yml``.  We support both.
        primary_path = os.path.join("src", "data", "conferences.yml")
        fallback_path = os.path.join("_data", "conferences.yml")

        data_path = primary_path if os.path.exists(primary_path) else fallback_path

        existing: List[Dict[str, Any]] = []
        if os.path.exists(data_path):
            with open(data_path, "r") as f:
                existing = yaml.safe_load(f) or []

        added_count = 0
        for cand in candidates:
            # Check for duplicates based on title and year
            if any(ent.get("title") == cand.title and ent.get("year") == cand.year for ent in existing):
                continue

            entry: Dict[str, Any] = {
                "title": cand.title,
                "year": cand.year or datetime.now().year + 1,
                "id": self._generate_conference_id(cand.title, cand.year or datetime.now().year + 1),
                "full_name": cand.full_name or cand.title,
                "link": cand.url,
                "deadline": self._parse_deadline(cand.deadline),
                "timezone": "AoE",  # Default to anywhere on Earth time
                "date": cand.conference_date,
                "tags": cand.tags,
                "city": cand.city,
                "country": cand.country,
                "note": f"Auto‑discovered from {cand.source}. Please verify details."
            }
            if cand.abstract_deadline:
                entry["abstract_deadline"] = self._parse_deadline(cand.abstract_deadline)

            existing.append(entry)
            added_count += 1

        if added_count == 0:
            return 0

        # Sort by deadline to keep the file neat
        existing.sort(key=lambda x: x.get("deadline", "9999"))

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

        return added_count

    # -------------------------------------------------------------------------
    # Scraping helpers
    # -------------------------------------------------------------------------
    def _scrape_wikicfp(self) -> List[ConferenceCandidate]:
        """Scrape the WikiCFP website for candidate conferences."""
        base_url = "http://www.wikicfp.com/cfp/"
        candidates: List[ConferenceCandidate] = []
        for category, keywords in TARGET_CATEGORIES.items():
            for keyword in keywords[:2]:  # Limit to first two keywords for speed
                search_url = f"{base_url}servlet/tool.search?q={keyword.replace(' ', '+')}&year=f"
                response = self._safe_request(search_url)
                if not response:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                candidates += self._parse_wikicfp_results(soup, category)
                # Be respectful of the website
                time.sleep(1)
        return candidates

    def _parse_wikicfp_results(self, soup: BeautifulSoup, category: str) -> List[ConferenceCandidate]:
        """Parse the search result table on WikiCFP into candidates."""
        results: List[ConferenceCandidate] = []
        rows = soup.find_all("tr")[1:10]  # Skip header and limit number of rows
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            title_cell, deadline_cell, location_cell = cells[:3]
            title_link = title_cell.find("a")
            if not title_link:
                continue
            title = title_link.get_text(strip=True)
            url = urljoin("http://www.wikicfp.com/cfp/", title_link.get("href", ""))
            candidate = ConferenceCandidate(
                title=title,
                url=url,
                deadline=deadline_cell.get_text(strip=True),
                location=location_cell.get_text(strip=True),
                tags=[category],
                source="WikiCFP",
            )
            # Attempt to extract more details from the individual conference page
            self._enhance_from_wikicfp_page(candidate)
            results.append(candidate)
        return results

    def _enhance_from_wikicfp_page(self, candidate: ConferenceCandidate) -> None:
        """Fetch additional details from a specific conference page on WikiCFP."""
        response = self._safe_request(candidate.url)
        if not response:
            return
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract year and description
        # The page structure may vary but we look for some common patterns
        # Deadline and event date extraction from the details table
        for row in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) >= 2:
                key, value = cells[0].lower(), cells[1]
                if "when" in key:
                    candidate.conference_date = value
                elif "submission deadline" in key:
                    candidate.deadline = value
                elif "where" in key:
                    candidate.location = value
        # Attempt to parse year from the conference date or deadline
        for text in [candidate.conference_date, candidate.deadline]:
            match = re.search(r"(20\d{2})", text or "")
            if match:
                candidate.year = int(match.group(1))
                break
        # Description could be the first paragraph
        p = soup.find("p")
        if p:
            candidate.description = p.get_text(strip=True)[:500]

    # -------------------------------------------------------------------------
    # AI Enhancement
    # -------------------------------------------------------------------------
    def _ai_enhance_candidates(self, candidates: List[ConferenceCandidate]) -> List[ConferenceCandidate]:
        """Use a Gemini model to categorise and enrich candidates.

        If the Gemini SDK is unavailable or no API key is provided, the
        candidates will be returned unmodified.
        """
        if genai is None or not self.gemini_api_key:
            if genai is None:
                print("⚠️  google-generativeai package not installed; skipping AI enhancement")
            elif not self.gemini_api_key:
                print("⚠️  GEMINI_API_KEY not provided; skipping AI enhancement")
            return candidates

        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        except Exception as e:
            print(f"⚠️  Failed to initialise Gemini model: {e}")
            return candidates

        enhanced: List[ConferenceCandidate] = []
        for cand in candidates:
            # Prepare a prompt describing the conference and requesting structured data
            prompt = (
                f"Analyze this conference information and respond in JSON:\n"
                f"Title: {cand.title}\n"
                f"Description: {cand.description}\n"
                f"Location: {cand.location}\n"
                f"Current Tags: {cand.tags}\n\n"
                "Provide a JSON object with the following keys:\n"
                "categories: a list of the most appropriate categories from: "
                f"{list(TARGET_CATEGORIES.keys())};\n"
                "confidence_score: a number between 0 and 1 representing confidence that this is a legitimate AI conference;\n"
                "full_name: the full expanded conference name;\n"
                "city: the city where the conference takes place;\n"
                "country: the country where the conference takes place;\n"
                "year: the year of the conference (integer)."
            )
            try:
                response = model.generate_content(prompt)
                # The SDK returns an object with a `.text` attribute containing
                # the raw response.  We expect this to be valid JSON.
                content = response.text if hasattr(response, "text") else str(response)
                data = json.loads(content)
                # Update candidate with AI insights
                cand.tags = data.get("categories", cand.tags)
                cand.confidence_score = float(data.get("confidence_score", 0.5))
                cand.full_name = data.get("full_name", cand.title)
                cand.city = data.get("city", cand.city)
                cand.country = data.get("country", cand.country)
                cand.year = int(data.get("year", cand.year or datetime.now().year + 1))
            except Exception as e:
                # If any error occurs (network, parsing etc.) we keep the original candidate
                print(f"Error enhancing {cand.title}: {e}")
            enhanced.append(cand)
            # Respect API rate limits
            time.sleep(0.5)
        return enhanced

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------
    def _filter_candidates(self, candidates: List[ConferenceCandidate]) -> List[ConferenceCandidate]:
        """Filter out candidates that are low confidence or clearly invalid."""
        current_year = datetime.now().year
        next_year = current_year + 1
        filtered: List[ConferenceCandidate] = []
        # Load existing conferences to avoid duplicates
        existing_titles = {entry.get("title", ""): entry.get("year") for entry in self._load_existing_conferences()}
        for cand in candidates:
            if cand.confidence_score < 0.6:
                continue
            if len(cand.title) < 3:
                continue
            if not cand.tags:
                continue
            # Require conference to be this year or next year
            if cand.year not in (current_year, next_year):
                continue
            if existing_titles.get(cand.title) == cand.year:
                continue
            filtered.append(cand)
        return filtered

    def _load_existing_conferences(self) -> List[Dict[str, Any]]:
        """Load existing conferences from YAML to avoid duplicates."""
        primary = os.path.join("src", "data", "conferences.yml")
        fallback = os.path.join("_data", "conferences.yml")
        path = primary if os.path.exists(primary) else fallback
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or []
        except FileNotFoundError:
            return []

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def _safe_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Perform an HTTP GET request with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as exc:
            print(f"Request failed for {url}: {exc}")
            return None

    def _generate_conference_id(self, title: str, year: int) -> str:
        """Generate a simple ID from the conference title and year."""
        # Use acronym from capital letters or first letters of first two words
        words = title.split()
        acronym = "".join([word[0].lower() for word in words if word[0].isalpha()])
        if len(acronym) < 2:
            cleaned = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
            acronym = cleaned[:4]
        return f"{acronym}{str(year)[-2:]}"

    def _parse_deadline(self, deadline_str: str) -> str:
        """Normalise various deadline formats into ISO‑like strings."""
        if not deadline_str:
            return ""
        # Known patterns: 'YYYY-MM-DD', 'Month DD, YYYY', 'DD/MM/YYYY'
        # Attempt to parse them sequentially
        patterns = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%d/%m/%Y",
        ]
        for fmt in patterns:
            try:
                dt = datetime.strptime(deadline_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d 23:59:59")
            except Exception:
                continue
        # Fallback: return the string as is
        return deadline_str


if __name__ == "__main__":
    engine = ConferenceDiscoveryEngine()
    new_candidates = engine.discover_conferences()
    added = engine.add_to_conferences_yml(new_candidates)
    print(f"✅ Added {added} conferences to conferences.yml")  
