import yaml
from datetime import datetime
import sys
import urllib.request # Using standard library to avoid dependency issues

# URL for the YAML data
yaml_url = "https://raw.githubusercontent.com/gak97/ai-deadlines-mm/gh-pages/_data/conferences.yml"
yaml_data_str = ""

try:
    with urllib.request.urlopen(yaml_url) as response:
        if response.status == 200:
            yaml_data_str = response.read().decode('utf-8')
        else:
            print(f"Error fetching YAML from URL: HTTP {response.status}")
            sys.exit(1)
except Exception as e:
    print(f"Error fetching YAML from URL: {e}")
    sys.exit(1)

# Load YAML data
try:
    conferences_data = yaml.safe_load(yaml_data_str)
    if conferences_data is None: 
        conferences_data = []
except yaml.YAMLError as e:
    print(f"Error parsing YAML: {e}")
    # Print some context if parsing fails
    # context_lines = 20
    # if e.problem_mark:
    #     start_line = max(0, e.problem_mark.line - context_lines // 2)
    #     end_line = min(len(yaml_data_str.splitlines()), e.problem_mark.line + context_lines // 2 +1)
    #     print("Problematic YAML snippet (lines approx {} to {}):".format(start_line, end_line))
    #     print("\n".join(yaml_data_str.splitlines()[start_line:end_line]))
    conferences_data = []
    sys.exit(1) # Exit if YAML parsing fails
except Exception as ex:
    print(f"An unexpected error occurred during YAML parsing: {ex}")
    conferences_data = []
    sys.exit(1) # Exit if YAML parsing fails


# Target conferences
target_conferences = [
    "NeurIPS", "ICLR", "ICML", "ACL", "EACL", "NAACL", "AACL", "CVPR", "ICCV", "ECCV", "ACM WWW", "ACM MM"
]

# Current date for comparison (late July 2024)
current_date = datetime(2024, 7, 31)

# Helper function to parse deadline strings
def parse_deadline(deadline_str):
    if not deadline_str or deadline_str == 'N/A':
        return None
    formats_to_try = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
    ]
    original_deadline_str = str(deadline_str) # for logging if parsing fails
    
    # Pre-process to handle timezones if they are part of the string but not part of the format
    # This is a simplified approach; robust timezone parsing is complex.
    processed_deadline_str = original_deadline_str
    tz_indicators = [" UTC", " GMT", " PST", " PDT", " EST", " EDT", " CET", " CEST"] # Add more as needed
    for tz in tz_indicators:
        if tz in processed_deadline_str:
            processed_deadline_str = processed_deadline_str.split(tz)[0]
    # Handle cases like '2024-10-10 23:59:59 UTC-12' -> '2024-10-10 23:59:59'
    if isinstance(processed_deadline_str, str) and processed_deadline_str.count(' ') > 1 and ('-' in processed_deadline_str.split(' ')[-1] or '+' in processed_deadline_str.split(' ')[-1]):
        processed_deadline_str = " ".join(processed_deadline_str.split(' ')[:-1])


    for fmt in formats_to_try:
        try:
            return datetime.strptime(processed_deadline_str.strip(), fmt)
        except ValueError:
            continue
    # print(f"Warning: Could not parse deadline string: '{original_deadline_str}' as '{processed_deadline_str}' with known formats.")
    return None

# Group conferences by title
grouped_conferences = {}
if isinstance(conferences_data, list):
    for conf in conferences_data:
        if not isinstance(conf, dict):
            continue
        title = conf.get('title', '')
        if not title:
            continue
        
        title_lower = title.lower().strip()
        if '[' in title_lower: # Handle titles like "NeurIPS [Dataset and Benchmarks Track]"
            title_lower = title_lower.split('[')[0].strip()

        if title_lower not in grouped_conferences:
            grouped_conferences[title_lower] = []
        grouped_conferences[title_lower].append(conf)
        
        # Handle specific known aliases
        if title_lower == "the web conference":
            if "www" not in grouped_conferences: grouped_conferences["www"] = []
            grouped_conferences["www"].append(conf)
        elif title_lower == "acm international conference on multimedia" or title_lower == "mm":
             if "mm" not in grouped_conferences: grouped_conferences["mm"] = []
             grouped_conferences["mm"].append(conf)
else:
    print("Warning: conferences_data is not a list after loading. Cannot group entries.")
    sys.exit(1)


results = []
for target_conf_name in target_conferences:
    target_conf_lower = target_conf_name.lower()
    display_name = target_conf_name
    
    conf_entries_to_check = []

    if target_conf_lower in grouped_conferences:
        conf_entries_to_check.extend(grouped_conferences[target_conf_lower])
    
    if target_conf_name == "ACM WWW":
        # Check common alias for ACM WWW
        if "www" in grouped_conferences and "www" != target_conf_lower :
            conf_entries_to_check.extend(grouped_conferences["www"])
            if not (target_conf_lower in grouped_conferences) : display_name = f"{target_conf_name} (found as 'WWW')"
    elif target_conf_name == "ACM MM":
        # Check common alias for ACM MM
        if "mm" in grouped_conferences and "mm" != target_conf_lower:
            conf_entries_to_check.extend(grouped_conferences["mm"])
            if not (target_conf_lower in grouped_conferences) : display_name = f"{target_conf_name} (found as 'MM')"

    unique_conf_entries = []
    seen_ids_or_full_entry = set()
    for entry in conf_entries_to_check:
        # Create a unique key for each entry to avoid duplicates from alias merging
        entry_key = entry.get('id', str(entry)) # Use 'id' if available, else string of dict
        if entry_key not in seen_ids_or_full_entry:
            unique_conf_entries.append(entry)
            seen_ids_or_full_entry.add(entry_key)
    
    conf_entries = unique_conf_entries
    report = ""

    if conf_entries:
        valid_entries = [e for e in conf_entries if isinstance(e.get('year'), (int, str)) and str(e.get('year')).isdigit() and int(str(e.get('year'))) >= 2020] # Basic sanity check for year
        if not valid_entries:
            report = f"{display_name}: Present but no valid/recent year found in entries."
            results.append(report)
            continue

        latest_entry = max(valid_entries, key=lambda x: int(str(x.get('year', 0))))
        
        conf_year_str = str(latest_entry.get('year', 'N/A'))
        deadline_str = str(latest_entry.get('deadline', 'N/A'))
        deadline_date = parse_deadline(deadline_str)
        
        effective_year = 0
        if conf_year_str.isdigit():
            effective_year = int(conf_year_str)
        
        conf_id = latest_entry.get('id', "")
        if isinstance(conf_id, str) and effective_year < 2023 : # Try to infer from ID if year is old or N/A
            year_digits_from_id = "".join([char for char in conf_id if char.isdigit()])
            if len(year_digits_from_id) >= 2 :
                potential_year_short = year_digits_from_id[-2:]
                if potential_year_short.isdigit():
                    potential_year_full = int("20" + potential_year_short)
                    if potential_year_full > effective_year: 
                        effective_year = potential_year_full
                        conf_year_str = str(effective_year) 

        report_year_info = conf_year_str
        report = f"{display_name} (Latest Entry Year: {report_year_info}): "
        
        if deadline_date:
            if deadline_date > current_date:
                report += f"Present and up-to-date. Deadline: {deadline_date.strftime('%Y-%m-%d %H:%M:%S')}."
            else: 
                if effective_year > current_date.year:
                     report += (f"Present (for {effective_year}), but the listed deadline "
                                f"{deadline_date.strftime('%Y-%m-%d %H:%M:%S')} has passed. "
                                f"This might be an old entry for a future conference. Data for {effective_year} might be outdated, check for {effective_year+1} details.")
                elif effective_year == current_date.year :
                     report += f"Present but likely outdated for current/next cycle. Deadline: {deadline_date.strftime('%Y-%m-%d %H:%M:%S')} (passed for {effective_year} iteration)."
                else: 
                     report += f"Outdated entry for {effective_year}. Deadline: {deadline_date.strftime('%Y-%m-%d %H:%M:%S')} (passed)."
        else: # No parseable deadline
            if effective_year > current_date.year:
                 report += f"Present (for {effective_year}). Deadline information unclear or missing ('{deadline_str}'), but year {effective_year} is in the future. Potentially up-to-date."
            elif effective_year == current_date.year:
                 report += f"Present (for {effective_year}) but deadline information is unclear ('{deadline_str}'). Could be outdated for current/next cycle."
            else: 
                 report += f"Outdated entry (Year: {report_year_info}). Deadline information missing or unclear ('{deadline_str}')."
    else:
        report = f"{display_name}: Missing entirely."
    results.append(report)

final_report_str = "\n".join(results)
print(final_report_str)

# Storing the summary in a variable for the submit_subtask_report tool
# This is just for demonstration if the output needs to be programmatically accessed.
global_summary_for_submission = final_report_str
