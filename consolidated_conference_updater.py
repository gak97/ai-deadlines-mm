#!/usr/bin/env python3
"""
Consolidated Conference Updater
===============================

This script combines multiple approaches to keep conference data up-to-date:

1. Fetches structured data from ccfddl/ccf-deadlines repository
2. Uses AI-powered discovery to find new conferences via Gemini
3. Falls back to web scraping for missing deadline information

The script writes to _data/conferences.yml for Jekyll compatibility.

Usage:
    python consolidated_conference_updater.py
"""

import os
import yaml
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import re

# Optional imports for AI and scraping features
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    from duckduckgo_search import DDGS
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

# Configuration
CONFERENCES_FILE = "_data/conferences.yml"
SEARCH_DELAY_SECONDS = 2
CURRENT_YEAR = datetime.now().year
YEARS_TO_SEARCH = [CURRENT_YEAR, CURRENT_YEAR + 1, CURRENT_YEAR + 2]

@dataclass
class ConferenceCandidate:
    """Representation of a potential conference."""
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

class ConsolidatedConferenceUpdater:
    """Main updater that coordinates all data sources."""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.conferences_file = CONFERENCES_FILE
        
    def update_conferences(self) -> None:
        """Main update process combining all data sources."""
        print("Starting consolidated conference update...")
        print(f"Current year: {CURRENT_YEAR}")
        print(f"Looking for conferences in years: {YEARS_TO_SEARCH}")
        
        # Load existing data
        existing_confs = self._load_existing_conferences()
        print(f"Loaded {len(existing_confs)} existing conferences")
        
        # Step 1: Fetch from CCF repository (most reliable)
        ccf_confs = self._fetch_ccf_data()
        if ccf_confs:
            print(f"Fetched {len(ccf_confs)} conferences from CCF repository")
            existing_confs = self._merge_conferences(existing_confs, ccf_confs)
        
        # Step 2: AI-powered discovery (if available)
        if GEMINI_AVAILABLE and self.gemini_api_key:
            ai_confs = self._discover_with_ai()
            if ai_confs:
                print(f"Discovered {len(ai_confs)} new conferences via AI")
                existing_confs = self._merge_conferences(existing_confs, ai_confs)
        
        # Step 3: Web scraping for missing data
        if SCRAPING_AVAILABLE:
            scraped_confs = self._scrape_missing_data(existing_confs)
            if scraped_confs:
                print(f"Scraped additional data for {len(scraped_confs)} conferences")
                existing_confs = self._merge_conferences(existing_confs, scraped_confs)
        
        # Save updated data
        self._save_conferences(existing_confs)
        print(f"Updated {self.conferences_file} with {len(existing_confs)} conferences")
    
    def _fetch_ccf_data(self) -> List[Dict[str, Any]]:
        """Fetch data from ccfddl repository."""
        try:
            api_url = "https://api.github.com/repos/ccfddl/ccf-deadlines/contents/conference/AI"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            conferences = []
            files_processed = 0
            for file in response.json():
                if file.get("name", "").endswith(".yml"):
                    files_processed += 1
                    yaml_content = requests.get(file["download_url"], timeout=10).text
                    conf_data = yaml.safe_load(yaml_content)
                    
                    # Handle both list and dict formats
                    if isinstance(conf_data, list) and conf_data:
                        conf_data = conf_data[0]  # Take first item from list
                    
                    if conf_data and isinstance(conf_data, dict) and "confs" in conf_data:
                        # CCF format: {confs: [...], title: "...", description: "..."}
                        conferences.append(conf_data)
            
            print(f"Processed {files_processed} YAML files, found {len(conferences)} conference series")
            return self._transform_ccf_data(conferences)
        except Exception as e:
            print(f"Error fetching CCF data: {e}")
            return []
    
    def _transform_ccf_data(self, raw_confs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform CCF data to our format."""
        transformed = []
        
        for conf in raw_confs:
            # CCF format: {confs: [...], title: "...", description: "..."}
            confs = conf.get("confs", [])
            if not confs:
                continue
            
            # Get future conferences (current year and beyond)
            future_confs = [c for c in confs if c.get("year", 0) >= CURRENT_YEAR]
            if not future_confs:
                continue
            
            # Debug output removed for cleaner logs
            
            for instance in future_confs:
                year = instance.get("year", CURRENT_YEAR)
                timeline = instance.get("timeline", [{}])[0] if instance.get("timeline") else {}
                
                entry = {
                    "id": instance.get("id", f"{conf.get('title', '').lower().replace(' ', '').replace('-', '')}{str(year)[-2:]}"),
                    "title": conf.get("title", ""),
                    "full_name": conf.get("description", ""),
                    "year": year,
                    "date": instance.get("date", ""),
                    "deadline": timeline.get("deadline", ""),
                    "abstract_deadline": timeline.get("abstract_deadline", ""),
                    "location": instance.get("place", ""),
                    "city": "",
                    "country": "",
                    "url": instance.get("link", ""),
                    "description": conf.get("description", ""),
                    "timezone": instance.get("timezone", ""),
                    "tags": [],
                    "source": "ccf"
                }
                
                # Parse location
                place = instance.get("place", "")
                if place and "," in place:
                    parts = place.split(",", 1)
                    entry["city"] = parts[0].strip()
                    entry["country"] = parts[1].strip()
                elif place:
                    entry["country"] = place.strip()
                
                # Parse dates
                if entry["date"]:
                    try:
                        start, end = self._parse_date_range(entry["date"], str(year))
                        entry["start"] = start
                        entry["end"] = end
                    except Exception as e:
                        print(f"Warning: Could not parse date '{entry['date']}' for {entry['title']}: {e}")
                
                transformed.append(entry)
        
        print(f"Transformed {len(transformed)} conference instances")
        return transformed
    
    def _discover_with_ai(self) -> List[Dict[str, Any]]:
        """Use AI to discover new conferences."""
        if not GEMINI_AVAILABLE or not self.gemini_api_key:
            return []
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Simple prompt to find new AI conferences
            prompt = f"""
            Find 5-10 new AI/ML conferences for {CURRENT_YEAR + 1} and {CURRENT_YEAR + 2} 
            that are not commonly known. Return as JSON array with fields:
            title, full_name, year, deadline, location, url, description
            """
            
            response = model.generate_content(prompt)
            # Parse response and convert to our format
            # This is a simplified version - the full AI discovery script has more sophisticated logic
            
            return []  # Placeholder - would implement full AI parsing here
            
        except Exception as e:
            print(f"Error in AI discovery: {e}")
            return []
    
    def _scrape_missing_data(self, existing_confs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape missing deadline information."""
        if not SCRAPING_AVAILABLE:
            return []
        
        scraped_data = []
        
        for conf in existing_confs:
            # Only scrape if missing deadline or dates
            if (not conf.get("deadline") or conf.get("deadline") == "TODO" or
                not conf.get("start") or conf.get("start") == "TODO"):
                
                if conf.get("url"):
                    print(f"Scraping missing data for {conf['title']} {conf['year']}")
                    time.sleep(SEARCH_DELAY_SECONDS)
                    
                    scraped_info = self._scrape_conference_website(conf["url"], conf["title"], conf["year"])
                    if scraped_info:
                        scraped_data.append(scraped_info)
        
        return scraped_data
    
    def _scrape_conference_website(self, url: str, title: str, year: int) -> Optional[Dict[str, Any]]:
        """Scrape conference information from website."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text(" ", strip=True).lower()
            
            # Basic scraping logic - would need to be enhanced for specific sites
            scraped_info = {
                "id": f"{title.lower().replace(' ', '').replace('-', '')}{str(year)[-2:]}",
                "title": title,
                "year": year,
                "url": url,
                "source": "scraped"
            }
            
            # Look for deadline patterns
            deadline_patterns = [
                r"submission.*deadline.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"deadline.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"due.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            ]
            
            for pattern in deadline_patterns:
                match = re.search(pattern, text_content)
                if match:
                    scraped_info["deadline"] = match.group(1)
                    break
            
            return scraped_info if scraped_info.get("deadline") else None
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def _parse_date_range(self, date_str: str, year: str) -> Tuple[str, str]:
        """Parse date range string into ISO dates."""
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

        # Replace abbreviations (use word boundaries to avoid partial matches)
        for abbr, full in month_map.items():
            start = re.sub(r'\b' + re.escape(abbr) + r'\b', full, start)
            end = re.sub(r'\b' + re.escape(abbr) + r'\b', full, end)

        start = " ".join(start.strip().split())
        end = " ".join(end.strip().split())

        try:
            start_dt = datetime.strptime(f"{start}, {year}", "%B %d, %Y")
            end_dt = datetime.strptime(f"{end}, {year}", "%B %d, %Y")
            return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Warning: Could not parse date range '{date_str}' for year {year}: {e}")
            return "", ""
    
    def _load_existing_conferences(self) -> List[Dict[str, Any]]:
        """Load existing conference data."""
        if not os.path.exists(self.conferences_file):
            return []
        try:
            with open(self.conferences_file, 'r') as f:
                data = yaml.safe_load(f)
                return data if data else []
        except Exception as e:
            print(f"Error loading conferences file: {e}")
            return []
    
    def _merge_conferences(self, existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge new conferences into existing list."""
        # Create index of existing conferences
        existing_index = {(c.get("title"), c.get("year")): i for i, c in enumerate(existing)}
        
        for conf in new:
            key = (conf.get("title"), conf.get("year"))
            if key in existing_index:
                # Update existing entry
                idx = existing_index[key]
                for field, value in conf.items():
                    if value:  # Only update non-empty values
                        existing[idx][field] = value
            else:
                # Add new entry
                existing.append(conf)
                existing_index[key] = len(existing) - 1
        
        return existing
    
    def _save_conferences(self, conferences: List[Dict[str, Any]]) -> None:
        """Save conferences to YAML file."""
        # Sort by deadline
        def sort_key(item: Dict[str, Any]) -> str:
            return item.get("deadline", "9999") or "9999"
        
        conferences.sort(key=sort_key)
        
        os.makedirs(os.path.dirname(self.conferences_file), exist_ok=True)
        with open(self.conferences_file, 'w') as f:
            yaml.dump(conferences, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point."""
    updater = ConsolidatedConferenceUpdater()
    updater.update_conferences()

if __name__ == "__main__":
    main() 