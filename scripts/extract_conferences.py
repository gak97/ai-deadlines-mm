import re
import yaml
from bs4 import BeautifulSoup
from pathlib import Path

INDEX_PATH = Path('index.html')

html = INDEX_PATH.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

script_text = '\n'.join(script.get_text('\n') for script in soup.find_all('script'))
blocks = script_text.split('// Process ')

deadline_map = {}
for block in blocks[1:]:
    lines = block.splitlines()
    if not lines:
        continue
    conf_id = lines[0].strip()
    match = re.search(r"var deadline = moment.tz\(([^,]+),\s*([^)]+)\);", block)
    if not match:
        continue
    deadline = match.group(1).strip().strip("'").strip('"')
    timezone = match.group(2).strip().strip("'").strip('"')
    deadline_map[conf_id] = {
        'deadline': deadline,
        'timezone': timezone,
    }

print('Captured', len(deadline_map), 'deadline entries')

records = []

CLASS_TO_TAG = {
    'ml-conf': 'ML',
    'cv-conf': 'CV',
    'cg-conf': 'CG',
    'nlp-conf': 'NLP',
    'ro-conf': 'RO',
    'sp-conf': 'SP',
    'dm-conf': 'DM',
    'ap-conf': 'AP',
    'kr-conf': 'KR',
    'hci-conf': 'HCI',
}

for conf_div in soup.select('div.ConfItem'):
    conf_id = conf_div.get('id')
    title_link = conf_div.select_one('.conf-title a')
    if title_link is None:
        continue
    title_text = title_link.get_text(strip=True)
    year = None
    title = title_text
    if title_text and title_text.split()[-1].isdigit():
        year = int(title_text.split()[-1])
        title = title_text.rsplit(' ', 1)[0]
    full_name = title_link.get('title', '').replace(' Details', '').strip()
    url_link = conf_div.select_one('.conf-title-icon a')
    url = url_link['href'] if url_link and url_link.has_attr('href') else ''
    date_span = conf_div.select_one('.conf-date')
    date = date_span.get_text(strip=True).rstrip('.') if date_span else ''
    place_link = conf_div.select_one('.conf-place a')
    location = place_link.get_text(strip=True) if place_link else ''
    note_div = conf_div.select_one('.note')
    note = note_div.get_text(strip=True) if note_div else ''
    abstract_div = conf_div.select_one('.abstract-deadline')
    abstract_deadline = ''
    if abstract_div:
        abstract_text = abstract_div.get_text(strip=True)
        match = re.search(r'(\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?)', abstract_text)
        if match:
            abstract_deadline = match.group(1)
    tags = []
    for cls in conf_div.get('class', []):
        if cls in CLASS_TO_TAG:
            tags.append(CLASS_TO_TAG[cls])
    deadline_info = deadline_map.get(conf_id, {})
    record = {
        'id': conf_id,
        'title': title,
        'year': year,
        'full_name': full_name,
        'url': url,
        'date': date,
        'location': location,
        'tags': tags,
    }
    if note:
        record['note'] = note
    if abstract_deadline:
        record['abstract_deadline'] = abstract_deadline
    if deadline_info.get('deadline'):
        record['deadline'] = deadline_info['deadline']
    if deadline_info.get('timezone'):
        record['timezone'] = deadline_info['timezone']
    records.append(record)

records.sort(key=lambda r: (r.get('deadline', '') or '', r['id']))
print('First few records after sort:', records[:3])

with open('_data/conferences.yml', 'w', encoding='utf-8') as f:
    yaml.dump(records, f, sort_keys=False, allow_unicode=True)
print('Wrote', len(records), 'records to _data/conferences.yml')
