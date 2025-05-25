import yaml
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import datetime
import os

# Constants
CONFERENCES_FILE = "_data/conferences.yml"
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
        # we might want to search for some default well-known conferences.
        # For this task, we assume conferences.yml has data.
        print("No existing conference titles found. This script currently relies on existing titles to search for updates.")
        # Example: seen_titles.update(["NeurIPS", "ICML", "CVPR", "ACL", "AISTATS"])

    for title in seen_titles:
        for year in YEARS_TO_SEARCH:
            targets.append({"title": title, "year": year})
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

        def find_info(keywords, default_val="TODO"):
            for keyword in keywords:
                try:
                    # Search for keyword in text, then try to get its parent or sibling text
                    # This is extremely naive. A real scraper would use specific element selectors.
                    found_elements = soup.find_all(string=lambda t: t and keyword in t.lower())
                    for el in found_elements:
                        # Try to get a meaningful chunk of text around the keyword.
                        # Heuristic: look at parent, and siblings.
                        # This needs to be much more robust for a real-world scraper.
                        potential_text_sources = [el.parent, el.parent.next_sibling, el.parent.previous_sibling]
                        for source_element in potential_text_sources:
                            if source_element and hasattr(source_element, 'get_text'):
                                parent_text = source_element.get_text(separator=' ', strip=True)
                                # Clean up text: remove excessive newlines/spaces
                                parent_text = ' '.join(parent_text.split())
                                if len(parent_text) > len(keyword) and len(parent_text) < 250: # Increased length limit
                                    # Check if the year is also mentioned nearby, increasing confidence
                                    # Also check for terms that might indicate it's the *correct* kind of info
                                    # (e.g., for "deadline", words like "date", "submission", specific months)
                                    if str(year) in parent_text or any(month in parent_text.lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                                        # Attempt to extract a more specific phrase rather than the whole parent_text
                                        # Try to find the sentence containing the keyword.
                                        # This is still very basic.
                                        sentences = parent_text.split('.') # Naive sentence split
                                        for sentence in sentences:
                                            if keyword in sentence.lower():
                                                extracted_phrase = sentence.strip()
                                                # Try to get a more specific snippet
                                                kw_idx = sentence.lower().find(keyword)
                                                # Look for text immediately following the keyword, common for deadlines/dates
                                                # e.g., "Deadline: September 1st" or "Location: Paris"
                                                snippet_after_keyword = sentence[kw_idx + len(keyword):].strip()
                                                # Remove leading colons, spaces
                                                snippet_after_keyword = snippet_after_keyword.lstrip(': ') 
                                                
                                                # Take up to a certain number of words or characters
                                                words_in_snippet = snippet_after_keyword.split()
                                                if len(words_in_snippet) > 0 and len(words_in_snippet) <= 10: # Up to 10 words
                                                    extracted_phrase = ' '.join(words_in_snippet)
                                                    # Basic sanity check: avoid overly long or very short (just punctuation) phrases
                                                    if len(extracted_phrase) > 3 and len(extracted_phrase) < 100:
                                                        print(f"Refined info for '{keyword}' (from '{el[:30]}...'): {extracted_phrase}")
                                                        return extracted_phrase

                                                # Fallback to sentence if specific snippet logic fails
                                                extracted_phrase = sentence.strip()
                                                if len(extracted_phrase) > 70: # If sentence is long, try to snippet around keyword
                                                    start_idx = max(0, kw_idx - 20) # shorter before keyword
                                                    end_idx = min(len(extracted_phrase), kw_idx + len(keyword) + 50) # longer after keyword
                                                    extracted_phrase = extracted_phrase[start_idx:end_idx].strip()
                                                
                                                print(f"Potential info for '{keyword}' (from '{el[:30]}...'): {extracted_phrase}")
                                                return extracted_phrase
                                        
                                        # Fallback if sentence splitting didn't work well but parent_text is plausible and contains keyword
                                        if keyword in parent_text.lower():
                                            kw_parent_idx = parent_text.lower().find(keyword)
                                            start_parent_idx = max(0, kw_parent_idx - 20)
                                            end_parent_idx = min(len(parent_text), kw_parent_idx + len(keyword) + 70) # more context
                                            contextual_parent_text = parent_text[start_parent_idx:end_parent_idx].strip()
                                            print(f"Potential info for '{keyword}' (context from parent for '{el[:30]}...'): {contextual_parent_text}")
                                            return contextual_parent_text
                        
                        # Fallback: if deep search in parent fails, try simpler text from element and its next few siblings
                        try:
                            current_el_text = el.get_text(strip=True)
                            if keyword in current_el_text.lower(): # keyword is in the element itself
                                combined_text = current_el_text
                                next_sib = el.next_sibling
                                count = 0
                                while next_sib and count < 3: # Look at next 3 siblings
                                    if hasattr(next_sib, 'get_text'):
                                        combined_text += " " + next_sib.get_text(strip=True)
                                    next_sib = next_sib.next_sibling
                                    count += 1
                                combined_text = ' '.join(combined_text.split()) # Clean spaces
                                if len(combined_text) > len(keyword) and len(combined_text) < 200:
                                     print(f"Potential info for '{keyword}' (element + siblings): {combined_text}")
                                     return combined_text
                        except:
                            pass


                except Exception as e_find:
                    # print(f"Minor error during find_info for {keyword}: {e_find}")
                    pass 
            return default_val

        # Attempt to find some common fields (keywords should be lowercase)
        deadline_keywords = ["submission deadline", "paper deadline", "full paper submission", "deadline", "papers due"]
        place_keywords = ["location", "venue", "city", "conference location", "held in"]
        date_keywords = ["conference dates", "dates", "when", "conference takes place"] # "when" is too generic alone
        
        deadline_str = find_info(deadline_keywords)
        place_str = find_info(place_keywords)
        date_str = find_info(date_keywords)
        
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
        if deadline_str.lower() in deadline_keywords and len(deadline_str) <= max(len(k) for k in deadline_keywords):
            deadline_str = "TODO" # Reset if it's just the keyword itself
        if place_str.lower() in place_keywords and len(place_str) <= max(len(k) for k in place_keywords):
            place_str = "TODO"
        if date_str.lower() in date_keywords and len(date_str) <= max(len(k) for k in date_keywords):
            date_str = "TODO"

        extracted_data = {
            "title": conference_title,
            "year": int(year),
            "id": conference_title.lower().replace(" ", "").replace("-", "") + str(year)[-2:],
            "link": url, # This is the page we scraped
            "deadline": deadline_str,
            "abstract_deadline": "TODO", # Still hard to find reliably without more specific patterns
            "timezone": "TODO", # TZ is often not explicitly on page or requires parsing relative times
            "place": place_str,
            "date": date_str,
            "start": "TODO", # Requires parsing 'date_str'
            "end": "TODO", # Requires parsing 'date_str'
            "sub": "TODO", # Subject area, very hard to find generically
            "note": f"Scraped from {url}" + (f". CFP: {cfp_link}" if cfp_link != "TODO" else "")
        }
        print(f"Scraped data for {conference_title} {year} from {url}: {{Deadline: {deadline_str}, Place: {place_str}, Date: {date_str}, CFP: {cfp_link}}}")
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

        if conf_id in existing_conf_map:
            print(f"Conference {conf_id} (from scraped/external data) found in existing data. Comparing...")
            current_conf = existing_conf_map[conf_id]
            
            # Update logic: Overwrite if new_info has more specific details for key fields
            # This is a basic heuristic. More sophisticated merging could be done.
            # Example: if current 'deadline' is 'TODO' and new one is not.
            updated = False
            for key in ["deadline", "place", "date", "start", "end", "link", "abstract_deadline", "timezone", "sub", "note"]:
                new_val = new_info.get(key)
                current_val = current_conf.get(key)
                if new_val and new_val != "TODO" and new_val is not None: # Check for meaningful new value
                    if current_val == "TODO" or current_val is None or current_val != new_val:
                        # Update if old value was placeholder or different
                        # More complex: for dates, check if newer if both are specific
                        current_conf[key] = new_val
                        updated = True
                        print(f"  Updating '{key}' for {conf_id} from '{current_val}' to '{new_val}'")
            
            if updated:
                print(f"Conference {conf_id} was updated with new information.")
            else:
                print(f"No meaningful updates for {conf_id} based on new data. Keeping existing.")
        else:
            # This is a new conference entry (e.g., for a future year not previously listed)
            print(f"Adding new conference to list: {conf_id} - {new_info.get('title')} {new_info.get('year')}")
            existing_data.append(new_info) # Append to the original list being modified
            existing_conf_map[conf_id] = new_info # Also add to map to prevent re-adding if duplicated in input list

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
