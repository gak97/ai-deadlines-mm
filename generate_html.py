#!/usr/bin/env python3
"""
HTML Generator for AI Conference Deadlines
==========================================

This script generates the HTML for the AI Conference Deadlines website
from the conferences.yml data file. It ensures that:

1. All conference information is displayed (dates, locations, notes, etc.)
2. Subject tags are properly applied for filtering
3. Abstract deadlines and notes are shown when available
4. The HTML structure matches the expected format

Usage:
    python generate_html.py
"""

import yaml
import os
from datetime import datetime
from typing import Dict, List, Any

def load_conferences() -> List[Dict[str, Any]]:
    """Load conferences from the YAML file."""
    with open('_data/conferences.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_conference_html(conf: Dict[str, Any]) -> str:
    """Generate HTML for a single conference."""
    conf_id = conf.get('id', '')
    title = conf.get('title', '')
    year = conf.get('year', '')
    full_name = conf.get('full_name', '')
    date = conf.get('date', '')
    location = conf.get('location', '')
    url = conf.get('url', '')
    tags = conf.get('tags', [])
    note = conf.get('note', '')
    abstract_deadline = conf.get('abstract_deadline', '')
    
    # Generate CSS classes for subject filtering
    tag_classes = ' '.join([f'{tag.lower()}-conf' for tag in tags]) if tags else ''
    
    # Generate subject tags HTML
    subject_tags_html = ''
    if tags:
        for tag in tags:
            tag_name = {
                'ML': 'Machine Learning',
                'CV': 'Computer Vision', 
                'CG': 'Computer Graphics',
                'NLP': 'Natural Language Proc',
                'RO': 'Robotics',
                'SP': 'Speech/SigProc',
                'DM': 'Data Mining',
                'AP': 'Automated Planning',
                'KR': 'Knowledge Representation',
                'HCI': 'Human-Computer Interaction'
            }.get(tag, tag)
            subject_tags_html += f'<span class="conf-sub" data-sub="{tag}">{tag_name}</span> '
    
    # Generate note HTML
    note_html = ''
    if note:
        note_html = f'<div class="note">{note}</div>'
    
    # Generate abstract deadline HTML
    abstract_html = ''
    if abstract_deadline and abstract_deadline != '':
        abstract_html = f'<div class="abstract-deadline">Abstract deadline: {abstract_deadline}</div>'
    
    # Generate location HTML
    location_html = ''
    if location:
        location_html = f'<a href="http://maps.google.com/?q={location}">{location}</a>'
    
    # Generate website link HTML
    website_html = ''
    if url:
        website_html = f'<a title="Conference Website" href="{url}" target="_blank"><img src="/ai-deadlines-mm/static/img/203-earth.svg" class="badge-link" alt="Link to Conference Website" /></a>'
    
    html = f'''
          <div id="{conf_id}" class="ConfItem {tag_classes}">
            <div class="row conf-row">
                <div class="col-6">
                  <span class="conf-title">
                      <a title="{full_name} Details" href="/ai-deadlines-mm/conference?id={conf_id}">{title} {year}</a>
                  </span>
                  <span class="conf-title-small">
                      <a title="{full_name} Details" href="/ai-deadlines-mm/conference?id={conf_id}">{title} '{str(year)[-2:]}</a>
                  </span>
                  <span class="conf-title-icon">
                    {website_html}
                    &ZeroWidthSpace;
                    
                    &ZeroWidthSpace;
                    
                    &ZeroWidthSpace;
                  </span>
                </div>
                <div class="col-6">
                  <span class="timer"></span>
                  <span class="timer-small"></span>
                </div>
            </div>
            <div class="row">
              <div class="col-12 col-sm-6">
                <div class="meta">
                  <span class="conf-date">{date}.</span>
                  <span class="conf-place">
                    {location_html}.
                  </span>
                </div>
                {note_html}
                {abstract_html}
                <div class="conf-subjects">
                  {subject_tags_html}
                </div>
              </div>
              <div class="col-12 col-sm-6">
                <div class="deadline">
                  <div>Deadline:
                    <span class="deadline-time"></span>
                  </div>
                </div>
                <div class="calendar"></div>
              </div>
            </div>
            <div class="row">
              <div class="col-12">
                
              </div>
            </div>
            <hr>
          </div>
'''
    return html

def generate_main_html():
    """Generate the main index.html file."""
    conferences = load_conferences()
    
    # Sort conferences by deadline
    conferences.sort(key=lambda x: x.get('deadline', ''))
    
    # Generate HTML for each conference
    conference_html = ''
    for conf in conferences:
        conference_html += generate_conference_html(conf)
    
    # Generate JavaScript for conference data processing
    conference_data_js = generate_conference_data_js(conferences)
    
    # Read the template HTML
    with open('index_template.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Replace the placeholder with generated conference HTML
    final_html = template.replace('{{CONFERENCES}}', conference_html)
    final_html = final_html.replace('// Conference data and processing will be added here by the generation script', conference_data_js)
    
    # Write the final HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Generated HTML for {len(conferences)} conferences")

def generate_conference_data_js(conferences):
    """Generate JavaScript for conference data processing."""
    js_lines = []
    
    for conf in conferences:
        conf_id = conf.get('id', '')
        deadline = conf.get('deadline', '')
        timezone = conf.get('timezone', 'UTC-12')
        
        if deadline and deadline != '':
            js_lines.append(f'''
        // Process {conf_id}
        if (typeof moment !== 'undefined') {{
          var deadline = moment.tz('{deadline}', '{timezone}');
          var now = moment();
          var diff = deadline.diff(now, 'seconds');
          
          $('#{conf_id}').attr("diff", diff);
          $('#{conf_id} .deadline-time').text(deadline.format('ddd MMM DD YYYY HH:mm:ss [GMT]Z'));
          
          if (diff > 0) {{
            $('#{conf_id} .timer').countdown(deadline.toDate(), function(event) {{
              $(this).html(event.strftime('%D days %H:%M:%S'));
            }});
            $('#{conf_id} .timer-small').countdown(deadline.toDate(), function(event) {{
              $(this).html(event.strftime('%D days %H:%M:%S'));
            }});
          }} else {{
            $('#{conf_id}').addClass('past');
            $('#{conf_id}').appendTo($("#past_confs"));
            $('#{conf_id} .timer').replaceWith($('#{conf_id} .deadline'));
            $('#{conf_id} .timer-small').replaceWith($('#{conf_id} .deadline'));
            $('#{conf_id} .calendar').remove();
          }}
        }}''')
    
    return '\n'.join(js_lines)

def main():
    """Main function."""
    print("Generating HTML from conferences.yml...")
    generate_main_html()
    
    # Also generate conference detail pages
    print("Generating conference detail pages...")
    import subprocess
    subprocess.run(["python", "generate_conference_pages.py"], check=True)
    
    print("HTML generation complete!")

if __name__ == "__main__":
    main()
