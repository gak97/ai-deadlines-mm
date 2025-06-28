import yaml
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
import time # Added for delay
from dateutil import parser as date_parser
from dateutil.parser import ParserError

# Constants
CONFERENCES_FILE = "_data/conferences.yml"
SEARCH_DELAY_SECONDS = 2 # Delay between DDG searches
CURRENT_YEAR = datetime.datetime.now().year
YEARS_TO_SEARCH = [CURRENT_YEAR + 1, CURRENT_YEAR + 2]

def load_existing_data(filepath):
    """Loads conference data from a YAML file."""
    print(f"Loading existing data from {filepath}...")
    if not os.path.exists(filepath):
        print(f"File {filepath} not found. Initializing empty list.")
        return []
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            if data is None: # Handle empty file
                return []
            return data
    except Exception as e:
        print(f"Error loading YAML file {filepath}: {e}")
        return []

def identify_target_conferences(conference_data):
    """Identifies conference titles and target years."""
    print("Identifying target conferences and years...")
    targets = []
    # Assuming conference_data is a list of dicts, each with a 'title'
    # We want to find info for unique conference titles for future years.
    seen_titles = set()
    for conf in conference_data:
        if 'title' in conf:
            seen_titles.add(conf['title'])

    # If the file was empty or no titles found, we might need a default list or another strategy.
    # For now, let's assume some titles are present or we add some common ones.
    # This part might need adjustment based on how we want to discover *new* conference series.
    if not seen_titles:
        # Fallback: if conferences.yml is empty or has no titles,
        # use a list of well-known AI conferences so the script can
        # bootstrap a fresh dataset. This prevents the updater from
        # immediately exiting on a new repo checkout.
        print(
            "No existing conference titles found. Using default conference list "
            "to bootstrap data."
        )
        # Add AAAI to the default list for bootstrapping
        seen_titles.update(["NeurIPS", "ICML", "AISTATS", "CVPR", "ACL", "AAAI"])

    for title in seen_titles:
        for year_to_search in YEARS_TO_SEARCH:
            targets.append({"title": title, "year": year_to_search})

    print(f"Identified {len(targets)} target conference instances to search.")
    return targets

def search_conference_websites(conference_title, year):
    """Searches for official conference websites using DuckDuckGo."""
    query = f"{conference_title} {year} official website"
    print(f"Searching for: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
        print(f"Found {len(results)} results for {query}.")
        return [result['href'] for result in results]
    except Exception as e:
        print(f"Error during DuckDuckGo search for {query}: {e}")
        return []

def scrape_conference_info(url, conference_title, year):
    """Scrapes conference information from a given URL."""
    print(f"Scraping: {url} for {conference_title} {year}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')

        # Placeholder for actual scraping logic
        # This will be highly specific and fragile
        # For now, just returning a dummy structure
        print(f"Successfully fetched content from {url}. Parsing...")

        # --- Actual Scraping Logic ---
        # This is a very basic attempt and will need significant refinement.
        text_content = soup.get_text(" ", strip=True).lower()
        page_title_text = (soup.title.string if soup.title else "").lower()

        # Confirm relevance (basic check)
        if not (conference_title.lower() in page_title_text or conference_title.lower() in text_content) or \
           not str(year) in text_content:
            # print(f"Content of {url} does not seem to match {conference_title} {year} based on title/year presence.")
            # Pass for now, maybe some sites don't mention it prominently.
            pass

        def parse_date_range(date_str_in, year_context):
            """
            Parses a date string which might be a range (e.g., "Jan 20-27, 2026", "20-27 January 2026")
            Returns (start_date, end_date) as YYYY-MM-DD strings or (None, None) if parsing fails.
            """
            if not date_str_in or any(tba.lower() in date_str_in.lower() for tba in ["tba", "tbd", "announced soon", "coming soon"]):
                return None, None

            date_str_in = date_str_in.replace("–", "-").replace("—", "-") # Normalize dashes

            # Common patterns:
            # 1. Month Day-Day, Year (e.g., January 20-27, 2026)
            # 2. Day-Day Month Year (e.g., 20-27 January 2026)
            # 3. Month Day - Month Day, Year (e.g. January 20 - February 2, 2026)
            # 4. Month Day, Year - Month Day, Year (e.g. January 20, 2026 - January 27, 2026)
            # 5. Month Day (assume current year_context if not specified, then cross-check)

            start_date_obj, end_date_obj = None, None

            try:
                # Try direct parsing if it's a single date or already well-formed range
                # date_parser is good but might misinterpret "Jan 20-27" without context
                # Add year context if missing in parts of the string
                if str(year_context) not in date_str_in:
                    date_str_with_year = f"{date_str_in}, {year_context}"
                else:
                    date_str_with_year = date_str_in

                # Pattern 1 & 2: "Month Day1-Day2, Year" or "Day1-Day2 Month Year"
                # e.g. "January 20-27, 2026", "20-27 January 2026"
                match_month_day_range = re.search(r"([a-zA-Z]+)\s*(\d{1,2})\s*-\s*(\d{1,2})\s*,?\s*(\d{4})", date_str_in, re.IGNORECASE)
                if not match_month_day_range:
                     match_day_range_month = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})\s*([a-zA-Z]+)\s*,?\s*(\d{4})", date_str_in, re.IGNORECASE)
                     if match_day_range_month:
                         # Reformat to Month Day-Day, Year for consistent parsing by date_parser
                         # Example: "20-27 January 2026" -> "January 20-27 2026"
                         m = match_day_range_month.groups()
                         date_str_with_year = f"{m[2]} {m[0]}-{m[1]}, {m[3]}"


                # More complex range: "Month1 Day1 - Month2 Day2, Year" or "Month Day1, Year1 - Month Day2, Year2"
                # Split by common range separators like " - "
                parts = re.split(r'\s+-\s+', date_str_with_year)
                if len(parts) == 2:
                    start_str, end_str = parts[0].strip(), parts[1].strip()

                    # If end_str is just a day, it implies same month and year as start_str
                    # e.g. "January 20 - 27, 2026"
                    if re.match(r"^\d{1,2}$", end_str) and str(year_context) in start_str: # "27"
                         # find month in start_str
                        start_month_match = re.search(r"([a-zA-Z]+)", start_str)
                        if start_month_match:
                            end_str = f"{start_month_match.group(1)} {end_str}, {year_context}"

                    # If end_str has month but no year, use year from start_str or year_context
                    # e.g., "January 20 - February 2, 2026" (year is already there)
                    # or "Jan 20, 2026 - Feb 2"
                    if not re.search(r"\d{4}", end_str): # No year in end_str
                        year_in_start = re.search(r"(\d{4})", start_str)
                        if year_in_start:
                            end_str = f"{end_str}, {year_in_start.group(1)}"
                        else: # fallback to general year context
                            end_str = f"{end_str}, {year_context}"

                    # If start_str has no year, add from end_str or year_context
                    if not re.search(r"\d{4}", start_str):
                        year_in_end = re.search(r"(\d{4})", end_str)
                        if year_in_end:
                             start_str = f"{start_str}, {year_in_end.group(1)}"
                        else: # fallback to general year context
                             start_str = f"{start_str}, {year_context}"

                    try:
                        start_date_obj = date_parser.parse(start_str)
                        end_date_obj = date_parser.parse(end_str)
                    except ParserError:
                        # Fallback to trying to parse the whole string if split logic failed
                        start_date_obj, end_date_obj = None, None # reset

                if not start_date_obj: # If not parsed by range logic above, try to parse the reconstructed string
                    try:
                        # Attempt to parse the most complete date string we've constructed so far
                        # This will handle single dates or well-formed date strings that don't fit explicit range regexes
                        start_date_obj = date_parser.parse(date_str_with_year)
                        end_date_obj = start_date_obj # Assume single day if only one date parsed this way
                        print(f"Parsed as single date: {start_date_obj} from '{date_str_with_year}'")

                        # Check if the original input string `date_str_in` looks more like a range
                        # that `date_parser.parse` might have only partially understood.
                        # This is a simplified check.
                        if '-' in date_str_in and start_date_obj:
                            # Try to see if we can parse a start and end from the original with more explicit regex
                            # This is a re-attempt at range parsing if the initial split failed but a dash is present.
                            # Example: "January 20-27, 2026" might be parsed as Jan 20 by default by `parse`.
                            # We need to guide it for ranges.

                            # Simplified regex for "Month Day-Day, Year" or "Day-Day Month Year"
                            # These are similar to what was tried before parts = re.split(...)
                            # This section is to catch cases where date_str_with_year might have been simplified too much
                            # or the split logic wasn't robust enough.

                            # Try "Month Day1-Day2, Year"
                            r_match = re.search(r"([a-zA-Z]+)\s*(\d{1,2})\s*-\s*(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})", date_str_in, re.IGNORECASE)
                            if r_match:
                                month, day1, day2, year_val = r_match.groups()
                                start_date_obj = date_parser.parse(f"{month} {day1}, {year_val}")
                                end_date_obj = date_parser.parse(f"{month} {day2}, {year_val}")
                                print(f"Re-parsed range (Month Day-Day, Year): {start_date_obj} to {end_date_obj}")
                            else:
                                # Try "Day1-Day2 Month Year"
                                r_match = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})(?:st|nd|rd|th)?\s*([a-zA-Z]+)\s*,?\s*(\d{4})", date_str_in, re.IGNORECASE)
                                if r_match:
                                    day1, day2, month, year_val = r_match.groups()
                                    start_date_obj = date_parser.parse(f"{month} {day1}, {year_val}")
                                    end_date_obj = date_parser.parse(f"{month} {day2}, {year_val}")
                                    print(f"Re-parsed range (Day-Day Month Year): {start_date_obj} to {end_date_obj}")

                    except (ParserError, TypeError, ValueError) as e_parse_single:
                        print(f"Could not parse date string '{date_str_in}' (tried as '{date_str_with_year}'): {e_parse_single}")
                        return None, None

            except (ParserError, TypeError, ValueError) as e_main: # Errors from initial attempts like re.split or early parse calls
                print(f"Error during main date string processing for '{date_str_in}': {e_main}")
                return None, None

            if start_date_obj and end_date_obj:
                # Validate year: if parsed year is far from context, it's likely an error or different event
                if abs(start_date_obj.year - year_context) > 2 or abs(end_date_obj.year - year_context) > 2:
                    # Allow one year off for conferences spanning New Year or announced very early/late
                    if not (abs(start_date_obj.year - year_context) <=1 and abs(end_date_obj.year - year_context) <=1 ):
                        print(f"Parsed date {start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')} year mismatch with context {year_context}. Discarding.")
                        return None, None
                return start_date_obj.strftime('%Y-%m-%d'), end_date_obj.strftime('%Y-%m-%d')

            return None, None


        def find_info(keywords, soup_doc, year_context_for_date, find_date_format=False):
            default_val = "TODO"
            for keyword in keywords:
                try:
                    # Search for keyword in text, then try to get its parent or sibling text
                    found_elements = soup_doc.find_all(string=lambda t: t and keyword in t.lower())
                    for el in found_elements:
                        potential_text_sources = [el.parent, el.parent.next_sibling, el.parent.previous_sibling]
                        if el.parent and el.parent.parent: # Look up two levels
                            potential_text_sources.append(el.parent.parent)

                        for source_element in potential_text_sources:
                            if source_element and hasattr(source_element, 'get_text'):
                                parent_text = source_element.get_text(separator=' ', strip=True)
                                parent_text_cleaned = ' '.join(parent_text.split())

                                if len(parent_text_cleaned) > len(keyword) and len(parent_text_cleaned) < 350: # Increased length limit
                                    # Check if the year is also mentioned nearby or a month, increasing confidence
                                    contains_year = str(year_context_for_date) in parent_text_cleaned
                                    contains_month = any(month in parent_text_cleaned.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])

                                    if contains_year or contains_month or find_date_format: # More lenient if we are specifically looking for dates
                                        sentences = parent_text_cleaned.split('.')
                                        for sentence in sentences:
                                            if keyword in sentence.lower() or find_date_format: # if find_date_format, keyword matching is less strict
                                                
                                                # Try to extract a relevant snippet
                                                kw_idx = sentence.lower().find(keyword) if keyword else -1
                                                
                                                # For dates, we want the text *after* the keyword or the date phrase itself
                                                if find_date_format:
                                                    # If keyword is "dates", "date", "when", the actual date is usually close
                                                    # Look for patterns like "Month Day-Day, Year" or "Day Month - Day Month Year"
                                                    # The parse_date_range function will handle various formats
                                                    # We need to pass it a candidate string.
                                                    # The sentence itself, or a part of it.
                                                    candidate_date_str = sentence
                                                    if kw_idx != -1 : # If keyword helped find this sentence
                                                        candidate_date_str = sentence[kw_idx + len(keyword):].lstrip(': ')

                                                    # Remove common prefixes like "Dates:", "Conference Dates:"
                                                    candidate_date_str = re.sub(r"^(conference dates|dates|date|when)\s*:\s*", "", candidate_date_str, flags=re.IGNORECASE).strip()

                                                    # Attempt to parse this candidate string
                                                    # print(f"Attempting to parse as date: '{candidate_date_str}' from sentence '{sentence}'")
                                                    # No, parse_date_range is called later with the result of find_info
                                                    # Here, we just return the string that seems to contain the date.

                                                    # Heuristic: good date strings are not too long, and contain digits and month names
                                                    if len(candidate_date_str) < 100 and any(char.isdigit() for char in candidate_date_str) and \
                                                       any(month in candidate_date_str.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                                                        print(f"Potential date phrase for '{keyword}': {candidate_date_str}")
                                                        return candidate_date_str.strip()

                                                else: # Not specifically finding a date string, general info extraction
                                                    snippet_after_keyword = sentence[kw_idx + len(keyword):].lstrip(': ')
                                                    words_in_snippet = snippet_after_keyword.split()
                                                    extracted_phrase = ' '.join(words_in_snippet[:15]) # Take up to 15 words

                                                    if len(extracted_phrase) > 3 and len(extracted_phrase) < 150 :
                                                        print(f"Refined info for '{keyword}': {extracted_phrase}")
                                                        return extracted_phrase.strip()
                                        
                                        # Fallback if sentence splitting didn't work, but parent_text is plausible
                                        if keyword in parent_text_cleaned.lower() or find_date_format:
                                            kw_parent_idx = parent_text_cleaned.lower().find(keyword) if keyword else -1

                                            if find_date_format:
                                                candidate_date_str = parent_text_cleaned
                                                if kw_parent_idx != -1:
                                                     candidate_date_str = parent_text_cleaned[kw_parent_idx + len(keyword):].lstrip(': ')
                                                candidate_date_str = re.sub(r"^(conference dates|dates|date|when)\s*:\s*", "", candidate_date_str, flags=re.IGNORECASE).strip()
                                                if len(candidate_date_str) < 100 and any(char.isdigit() for char in candidate_date_str) and \
                                                   any(month in candidate_date_str.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                                                    print(f"Potential date phrase (from parent_text) for '{keyword}': {candidate_date_str}")
                                                    return candidate_date_str.strip()
                                            else:
                                                contextual_parent_text = parent_text_cleaned[kw_parent_idx:] # From keyword onwards
                                                contextual_parent_text = ' '.join(contextual_parent_text.split()[:20]) # Limit length
                                                print(f"Potential info for '{keyword}' (context from parent): {contextual_parent_text}")
                                                return contextual_parent_text.strip()
                except Exception as e_find:
                    # print(f"Minor error during find_info for {keyword}: {e_find}")
                    pass
            return default_val

        # Attempt to find some common fields (keywords should be lowercase)
        # For dates, we'll do a more targeted search
        deadline_keywords = ["submission deadline", "paper deadline", "full paper submission", "deadline", "papers due", "abstracts due"]
        place_keywords = ["location", "venue", "city", "conference location", "held in", "takes place in"]
        # date_keywords are used to find a string, which is then parsed by parse_date_range
        date_text_keywords = ["conference dates", "dates:", "held from", "takes place from", "conference:", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        raw_date_str = find_info(date_text_keywords, soup, year, find_date_format=True)
        
        # Try to find date near conference title if previous failed
        if raw_date_str == "TODO":
            title_elements = soup.find_all(string=lambda t: t and conference_title.lower() in t.lower())
            for el in title_elements:
                parent = el.parent
                if parent:
                    parent_text = parent.get_text(" ", strip=True)
                    # Look for date like patterns near the title
                    # Example: "AAAI 2026 January 20-27, 2026"
                    # Or table rows/list items containing title and then date
                    # This is a simple proximity search
                    candidate_str = parent_text[parent_text.lower().find(conference_title.lower()):] # text from title onwards
                    # Limit length to avoid overly broad matches
                    candidate_str = ' '.join(candidate_str.split()[:20])

                    if str(year) in candidate_str and any(month.lower() in candidate_str.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                        # Remove the conference title itself from the candidate string to isolate date part
                        candidate_str = candidate_str.lower().replace(conference_title.lower(), "").strip()
                        # Remove year if it's at the beginning (e.g. "2026 January 20-27")
                        candidate_str = re.sub(r"^\d{4}\s*", "", candidate_str).strip()

                        print(f"Found candidate date string near title: '{candidate_str}'")
                        raw_date_str = candidate_str
                        break


        start_date, end_date = parse_date_range(raw_date_str, year)

        # If parse_date_range couldn't find it, try a more direct search for common text like "Month Day - Day, Year"
        if not start_date:
            all_text = soup.get_text(" ", strip=True)
            # Common date range patterns (simplified)
            # January 20 – 27, 2026  |  Jan 20-27, 2026 | 20-27 January 2026
            # This regex is very broad, parse_date_range will validate
            potential_date_matches = re.findall(r"([A-Za-z]+\s\d{1,2}(?:st|nd|rd|th)?\s*(?:–|-)\s*\d{1,2}(?:st|nd|rd|th)?\s*,\s*\d{4})", all_text, re.IGNORECASE) # Month Day-Day, Year
            if not potential_date_matches:
                 potential_date_matches = re.findall(r"(\d{1,2}(?:st|nd|rd|th)?\s*(?:–|-)\s*\d{1,2}(?:st|nd|rd|th)?\s*[A-Za-z]+\s\d{4})", all_text, re.IGNORECASE) # Day-Day Month Year
            if not potential_date_matches: # Month Day, Year - Month Day, Year
                 potential_date_matches = re.findall(r"([A-Za-z]+\s\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?\s*(?:–|-)\s*[A-Za-z]+\s\d{1,2}(?:st|nd|rd|th)?,\s*\d{4})", all_text, re.IGNORECASE)

            for potential_match in potential_date_matches:
                if str(year) in potential_match: # Ensure it's for the target year
                    print(f"Trying regex match for date: {potential_match}")
                    s, e = parse_date_range(potential_match, year)
                    if s and e:
                        raw_date_str = potential_match # Store the string that was successfully parsed
                        start_date, end_date = s, e
                        print(f"Date found via regex and parse_date_range: {start_date} to {end_date}")
                        break
        
        deadline_str = find_info(deadline_keywords, soup, year)
        place_str = find_info(place_keywords, soup, year)
        # The 'date' field in YAML was the string, keep it if parsed, else TODO
        date_yaml_str = raw_date_str if start_date and raw_date_str != "TODO" else "TODO"


        # Try to find a Call for Papers (CFP) link, often very informative
        cfp_link = "TODO"
        for link_tag in soup.find_all('a', href=True):
            link_text = link_tag.get_text(strip=True).lower()
            if "call for papers" in link_text or "cfp" in link_text:
                cfp_url = requests.compat.urljoin(url, link_tag['href'])
                print(f"Found potential CFP link: {cfp_url}")
                cfp_link = cfp_url
                break # Take the first one

        # Basic post-processing: if a found string is too generic like just "deadline" or "location"
        if deadline_str.lower() in deadline_keywords and len(deadline_str) <= max(len(k) for k in deadline_keywords) and deadline_str != "TODO":
            print(f"Resetting deadline from '{deadline_str}' to TODO as it's just a keyword.")
            deadline_str = "TODO"
        if place_str.lower() in place_keywords and len(place_str) <= max(len(k) for k in place_keywords) and place_str != "TODO":
            print(f"Resetting place from '{place_str}' to TODO as it's just a keyword.")
            place_str = "TODO"
        # date_yaml_str is already handled by being "TODO" if start_date is None

        extracted_data = {
            "title": conference_title,
            "year": int(year),
            "id": conference_title.lower().replace(" ", "").replace("-", "") + str(year)[-2:], # ID is titleYYYY (last 2 digits of year)
            "link": url,
            "deadline": deadline_str,
            "abstract_deadline": "TODO",
            "timezone": "TODO",
            "place": place_str,
            "date": date_yaml_str, # The original string that was parsed, or "TODO"
            "start": start_date if start_date else "TODO",
            "end": end_date if end_date else "TODO",
            "sub": "TODO",
            "note": f"Scraped from {url}" + (f". CFP: {cfp_link}" if cfp_link != "TODO" else "")
        }

        # Log the outcome of date parsing
        if start_date and end_date:
            print(f"Successfully parsed dates for {conference_title} {year}: {start_date} to {end_date} (from '{raw_date_str}')")
        else:
            print(f"Failed to parse specific start/end dates for {conference_title} {year} from '{raw_date_str}'. Date field will be '{date_yaml_str}'.")

        print(f"Scraped data for {conference_title} {year} from {url}: {{Deadline: {deadline_str}, Place: {place_str}, Date string: {date_yaml_str}, Start: {extracted_data['start']}, End: {extracted_data['end']}, CFP: {cfp_link}}}")
        return extracted_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
    except Exception as e:
        print(f"Error scraping URL {url}: {e}")
    return None


def update_yaml_data(existing_data, new_or_updated_conference_info_list):
    """Updates existing conference data with new information and adds new conferences."""
    print("Updating YAML data...")
    if not new_or_updated_conference_info_list:
        print("No new or updated conference information to process.")
        return existing_data

    # Create a dictionary of existing conferences by their ID for quick lookup and update
    existing_conf_map = {conf['id']: conf for conf in existing_data if 'id' in conf}

    for new_info in new_or_updated_conference_info_list:
        if not new_info or 'id' not in new_info:
            print(f"Skipping invalid new conference entry: {new_info}")
            continue

        conf_id = new_info['id']

        # Date finalization check
        has_finalized_dates = new_info.get('start') and new_info.get('start') != "TODO" and \
                              new_info.get('end') and new_info.get('end') != "TODO"

        if conf_id in existing_conf_map:
            current_conf = existing_conf_map[conf_id]
            print(f"Conference {conf_id} found in existing data. Comparing...")

            # Check if existing entry has finalized dates
            existing_has_finalized_dates = current_conf.get('start') and current_conf.get('start') != "TODO" and \
                                           current_conf.get('end') and current_conf.get('end') != "TODO"

            if not has_finalized_dates and existing_has_finalized_dates:
                print(f"  Scraped data for {conf_id} does not have finalized dates, but existing entry does. Preserving existing date info.")
                # Preserve existing date fields if new scrape doesn't have them
                new_info['date'] = current_conf.get('date', 'TODO')
                new_info['start'] = current_conf.get('start', 'TODO')
                new_info['end'] = current_conf.get('end', 'TODO')
            elif not has_finalized_dates and not existing_has_finalized_dates:
                 print(f"  Neither scraped nor existing data for {conf_id} has finalized dates. Will update other fields if possible but dates remain not finalized.")
            
            updated = False
            for key in ["deadline", "place", "date", "start", "end", "link", "abstract_deadline", "timezone", "sub", "note"]:
                new_val = new_info.get(key)
                current_val = current_conf.get(key)

                # Only update if new_val is meaningful ("TODO" or None is not meaningful for an update unless old value was also placeholder)
                if new_val is not None and new_val != "TODO":
                    if current_val == "TODO" or current_val is None or current_val != new_val:
                        current_conf[key] = new_val
                        updated = True
                        print(f"  Updating '{key}' for {conf_id} from '{current_val}' to '{new_val}'")
                elif key in ['start', 'end', 'date'] and new_val == "TODO" and current_val and current_val != "TODO":
                    # Don't overwrite a good date with TODO unless it's intentional (e.g. conference got postponed indefinitely)
                    # For now, the logic above (preserving existing dates if new ones are not final) handles this.
                    # This path means new_val is "TODO" but current_val is good. We should keep current_val.
                    # The preservation logic for dates already handled this specific case for start/end/date.
                    pass


            if updated:
                print(f"Conference {conf_id} was updated with new information.")
            else:
                print(f"No meaningful updates for {conf_id} based on new data. Keeping existing.")

        else: # New conference entry
            if has_finalized_dates:
                print(f"Adding new conference to list: {conf_id} - {new_info.get('title')} {new_info.get('year')} (Dates: {new_info.get('start')} to {new_info.get('end')})")
                existing_data.append(new_info)
                existing_conf_map[conf_id] = new_info
            else:
                print(f"Skipping adding new conference {conf_id} - {new_info.get('title')} {new_info.get('year')} as it does not have finalized dates. (Start: {new_info.get('start')}, End: {new_info.get('end')})")

    # Sort by year, then by title for consistent output
    # existing_data.sort(key=lambda x: (x.get('year', 0), x.get('title', '')))
    # The problem asks to match existing file's style, which might not be sorted like this.
    # For now, let's not aggressively re-sort the whole list if it's not required.
    # The key is that new items are added and existing ones are updated in place.
    return existing_data


def write_to_yaml(filepath, data):
    """Writes data to a YAML file."""
    print(f"Writing updated data to {filepath}...")
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            yaml.dump(data, f, Dumper=yaml.SafeDumper, sort_keys=False, width=1000, indent=2, default_flow_style=False)
        print("Successfully wrote to YAML file.")
    except Exception as e:
        print(f"Error writing YAML file {filepath}: {e}")

def main():
    """Main function to orchestrate the update process."""
    print("Attempting to update conference deadlines...")

    existing_conferences = load_existing_data(CONFERENCES_FILE)
    if existing_conferences is None: # Problem loading file
        print("Failed to load existing conference data. Aborting.")
        return

    target_searches = identify_target_conferences(existing_conferences)
    if not target_searches:
        print("No target conferences identified for search. Exiting.")
        write_to_yaml(CONFERENCES_FILE, existing_conferences) # Write back existing data
        print("Conference update process finished. No changes made as no targets were found.")
        return

    newly_scraped_or_updated_info = []
    processed_ids_for_current_run = set() # To avoid processing same id multiple times if search yields it

    for target in target_searches:
        conference_title = target["title"]
        year = target["year"]
        target_id = conference_title.lower().replace(" ", "").replace("-","") + str(year)[-2:]

        if target_id in processed_ids_for_current_run:
            continue # Already processed this ID in this run

        # Optimization: Check if a non-placeholder entry already exists for this exact ID
        # If so, we might only proceed if our scraping is intended to be very thorough for updates.
        # For now, the requirements imply we should search for future years.
        # The `update_yaml_data` will handle merging.
        
        # Let's check if this specific conference (title+year) already exists and has a deadline
        # This was the previous optimization logic.
        should_skip_search = False
        for conf in existing_conferences:
            if conf.get('id') == target_id:
                # Stricter check for skipping: only if deadline AND start/end dates are filled.
                # This means we are more likely to re-scrape if we only have partial info.
                deadline_present = conf.get('deadline') and isinstance(conf.get('deadline'), str) and conf.get('deadline').lower() != 'todo' and conf.get('deadline').strip() != ''
                start_date_present = conf.get('start') and conf.get('start') != 'TODO'
                end_date_present = conf.get('end') and conf.get('end') != 'TODO'
                
                # If we have a specific deadline AND specific start/end dates, consider it "detailed enough" to skip.
                if deadline_present and start_date_present and end_date_present:
                    print(f"Skipping active search for {conference_title} {year} (ID: {target_id}) as it has detailed deadline and date info already.")
                    should_skip_search = True
                    break
                # Allow re-scraping if only some fields are 'TODO' or placeholders from previous weak scrapes
                elif deadline_present and not (start_date_present and end_date_present):
                    print(f"Conference {target_id} has a deadline but no specific start/end dates. Will attempt to re-scrape for more details.")

        if should_skip_search:
            processed_ids_for_current_run.add(target_id)
            continue

        print(f"Waiting for {SEARCH_DELAY_SECONDS}s before next search to avoid rate limiting...")
        time.sleep(SEARCH_DELAY_SECONDS)
        urls = search_conference_websites(conference_title, year)
        found_info_for_target = False
        for url in urls:
            if any(skip_domain in url for skip_domain in ["linkedin.com", "researchgate.net", "facebook.com", "twitter.com", ".pdf"]):
                print(f"Skipping likely irrelevant or hard-to-parse URL: {url}")
                continue

            scraped_info = scrape_conference_info(url, conference_title, year)
            if scraped_info:
                # Ensure ID matches the target_id we are looking for.
                # Scraper generates ID, it should align with how target_id is generated.
                if scraped_info.get('id') != target_id:
                    print(f"Warning: Scraped ID {scraped_info.get('id')} does not match target ID {target_id}. Adjusting.")
                    scraped_info['id'] = target_id
                
                newly_scraped_or_updated_info.append(scraped_info)
                processed_ids_for_current_run.add(target_id)
                found_info_for_target = True
                break # Found info for this conference-year target from the first good URL
        
        if not found_info_for_target:
            print(f"No useful information found for {conference_title} {year} after checking {len(urls)} URLs.")
            processed_ids_for_current_run.add(target_id) # Mark as processed even if nothing found to avoid re-searching


    # `existing_conferences` is the baseline. `newly_scraped_or_updated_info` contains only items
    # that were actively searched for and yielded some scrape result in this run.
    final_conference_data = update_yaml_data(existing_conferences, newly_scraped_or_updated_info)
    
    # Sort data before writing for consistency, by year (desc) then title (asc)
    # This helps in reviewing diffs and keeping the file somewhat organized.
    # Ensure year is treated as int for sorting, title as string.
    final_conference_data.sort(key=lambda x: (x.get('year', 0) if isinstance(x.get('year'), int) else int(str(x.get('year',0))), x.get('title', '').lower()))


    write_to_yaml(CONFERENCES_FILE, final_conference_data)

    print("Conference update process finished. Check `_data/conferences.yml` for changes.")

if __name__ == "__main__":
    main()
