import sys
import urllib.request
from ruamel.yaml import YAML, representer

# URL for the YAML data
yaml_url = "https://raw.githubusercontent.com/gak97/ai-deadlines-mm/gh-pages/_data/conferences.yml"
yaml_data_str = ""

# --- Representer for multi-line strings to ensure literal style for 'note' ---
# class MyRepresenter(representer.RoundTripRepresenter):
#     pass

def str_presenter(dumper, data):
    if '\n' in data:  # Check for multi-line string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

# ruamel.yaml.representer.RoundTripRepresenter.add_representer(str, str_presenter)
# --- End of Representer setup ---

try:
    with urllib.request.urlopen(yaml_url) as response:
        if response.status == 200:
            yaml_data_str = response.read().decode('utf-8')
        else:
            # Critical errors should go to stderr if they prevent YAML output
            print(f"Error fetching YAML from URL: HTTP {response.status}", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f"Error fetching YAML from URL: {e}", file=sys.stderr)
    sys.exit(1)

yaml = YAML(typ='rt') # rt for round-trip, preserves comments/style
# yaml.Representer = MyRepresenter # Apply custom representer for note field - Re-enable if needed
yaml.representer.add_representer(str, str_presenter) # Correct way to add representer for str
yaml.indent(mapping=2, sequence=4, offset=2) 
yaml.preserve_quotes = True
yaml.width = 4096 # Prevent line wrapping for long strings like links

try:
    conferences_data = yaml.load(yaml_data_str)
    if conferences_data is None: 
        conferences_data = []
except Exception as e: 
    print(f"Error parsing YAML: {e}", file=sys.stderr)
    sys.exit(1)

# Define the new/updated NeurIPS 2025 entry
neurips_2025_data = {
    'title': 'NeurIPS',
    'year': 2025,
    'id': 'neurips25',
    'full_name': 'The Thirty-Ninth Annual Conference on Neural Information Processing Systems',
    'link': 'https://nips.cc/Conferences/2025/CallForPapers',
    'deadline': '2025-05-15 23:59:59',
    'abstract_deadline': '2025-05-11 23:59:59',
    'timezone': 'Etc/GMT+12', 
    'place': 'San Diego Convention Center',
    'date': 'December 2-7, 2025',
    'start': '2025-12-02',
    'end': '2025-12-07',
    'note': "Full Paper Submission Deadline May 15 '25 (Anywhere on Earth). Abstract deadline May 11 '25.",
    'sub': 'ML'
}

found_neurips_main_entry_index = -1
neurips_25_already_exists_and_updated = False

if isinstance(conferences_data, list):
    # First pass: check if neurips25 already exists and update it
    for i, conf in enumerate(conferences_data):
        if isinstance(conf, dict):
            conf_id_lower = str(conf.get('id', '')).lower().strip()
            if conf_id_lower == 'neurips25':
                # Update the existing neurips25 entry
                # Preserve original keys if they are not in the new data, but update all specified ones
                for key, value in neurips_2025_data.items():
                    conf[key] = value 
                # Ensure all keys from neurips_2025_data are present, remove others if necessary (policy decision)
                # For now, simple update is fine, which adds/overwrites keys.
                neurips_25_already_exists_and_updated = True
                found_neurips_main_entry_index = i 
                break 
    
    if not neurips_25_already_exists_and_updated:
        # If neurips25 was not found, try to find an older main NeurIPS entry to update (e.g., neurips24)
        candidate_to_update_index = -1
        # Prioritize updating 'neurips<YY>' (e.g. neurips24)
        for i, conf in enumerate(conferences_data):
            if isinstance(conf, dict):
                conf_title_lower = str(conf.get('title', '')).lower().strip()
                conf_id_lower = str(conf.get('id', '')).lower().strip()
                if conf_title_lower == 'neurips':
                    is_track_or_special = 'dbt' in conf_id_lower or \
                                          'workshop' in conf_id_lower or \
                                          'symposium' in conf_id_lower or \
                                          ('track' in conf_id_lower and not ('dataset' in conf_id_lower or 'benchmark' in conf_id_lower))
                    if not is_track_or_special:
                        if conf_id_lower.startswith('neurips') and conf_id_lower[len('neurips'):].isdigit():
                            candidate_to_update_index = i
                            break 
        
        # If no 'neurips<YY>' found, look for a generic 'neurips' id entry
        if candidate_to_update_index == -1:
            for i, conf in enumerate(conferences_data):
                if isinstance(conf, dict):
                    conf_title_lower = str(conf.get('title', '')).lower().strip()
                    conf_id_lower = str(conf.get('id', '')).lower().strip()
                    if conf_title_lower == 'neurips' and conf_id_lower == 'neurips':
                         is_track_or_special = 'dbt' in conf_id_lower or \
                                          'workshop' in conf_id_lower or \
                                          'symposium' in conf_id_lower or \
                                          ('track' in conf_id_lower and not ('dataset' in conf_id_lower or 'benchmark' in conf_id_lower))
                         if not is_track_or_special:
                            candidate_to_update_index = i
                            break
        
        if candidate_to_update_index != -1:
            # Update the identified existing entry
            conferences_data[candidate_to_update_index].update(neurips_2025_data)
            found_neurips_main_entry_index = candidate_to_update_index
        else:
            # Append as new if no suitable entry found to update
            last_neurips_related_index = -1
            for i, conf in reversed(list(enumerate(conferences_data))):
                if isinstance(conf, dict) and str(conf.get('title', '')).lower().strip() == 'neurips':
                    last_neurips_related_index = i
                    break
            if last_neurips_related_index != -1:
                conferences_data.insert(last_neurips_related_index + 1, neurips_2025_data)
            else:
                conferences_data.append(neurips_2025_data)
else:
    conferences_data = [neurips_2025_data] # Should not happen with valid conferences.yml

try:
    yaml.dump(conferences_data, sys.stdout)
except Exception as e:
    print(f"Error serializing YAML: {e}", file=sys.stderr)
    sys.exit(1)
