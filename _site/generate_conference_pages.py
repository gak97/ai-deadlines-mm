#!/usr/bin/env python3
"""
Conference Detail Page Generator
================================

This script generates dynamic conference detail pages that read from the conferences.yml
data and display all required information including date, location, and website links.

Usage:
    python generate_conference_pages.py
"""

import yaml
import os
from datetime import datetime
from typing import Dict, List, Any

def load_conferences() -> List[Dict[str, Any]]:
    """Load conferences from the YAML file."""
    with open('_data/conferences.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_conference_js_data(conferences: List[Dict[str, Any]]) -> str:
    """Generate JavaScript data for all conferences."""
    js_lines = []
    
    for conf in conferences:
        conf_id = conf.get('id', '')
        title = conf.get('title', '')
        year = conf.get('year', '')
        full_name = conf.get('full_name', '')
        date = conf.get('date', '')
        location = conf.get('location', '')
        url = conf.get('url', '')
        tags = conf.get('tags', [])
        deadline = conf.get('deadline', '')
        timezone = conf.get('timezone', 'UTC-12')
        note = conf.get('note', '')
        abstract_deadline = conf.get('abstract_deadline', '')
        
        # Generate subject tags
        subs_str = ','.join(tags) if tags else ''
        
        # Generate JavaScript for this conference
        js_lines.append(f'''
            if (conf == "{conf_id}") {{
              $(\'#conf-title-href\').text("{title} {year}");
              $(\'#conf-title-href\').attr(\'href\', "/ai-deadlines-mm/conference?id={conf_id}");
              $(\'#conf-full-name\').text("{full_name}");
              
              // set badges
              var subs = \'{subs_str}\'.split(\',\');
              for (let i = 0; i < subs.length; i++) {{
                var sub = subs[i].replace(" ", "");
                if (sub && sub2name[sub]) {{
                  var sub_element = document.createElement(\'span\');
                  sub_element.className = "conf-sub conf-" + sub;
                  sub_element.textContent = sub2name[sub];
                  $(\'#conf-subs\').append(sub_element);
                }}
              }}
              
              // conference details
              $(\'#conf-date\').text("{date}");
              $(\'#conf-place\').text("{location}");
              $(\'#conf-place\').attr(\'href\', "https://maps.google.com/?q={location}");
              $(\'#conf-website\').text("{url}");
              $(\'#conf-website\').attr(\'href\', "{url}");
              
              // Hide papers links if not available
              $(\'#conf-paperslink-div\').hide();
              $(\'#conf-pwclink-div\').hide();
              
              var twitter_slug = \'<a href="https://twitter.com/share" class="twitter-share-button" data-text="Countdown to the #{title}{year} deadline!" data-show-count="false" style="font-size:13px;">Tweet</a><script async src="//platform.twitter.com/widgets.js" charset="utf-8">\';
              $(\'#twitter-box\').html(twitter_slug);
              
              // Deadline processing
              if ("{deadline}" && "{deadline}" != "") {{
                // adjust date according to deadline timezone
                var timezone = "{timezone}";
                var confDeadline = moment.tz("{deadline}", timezone);

                // add calendar 
                var conferenceDeadlineCalendar = createCalendarFromObject({{
                  id: \'{conf_id}\',
                  title: \'{title} {year} deadline\',
                  date: confDeadline.toDate(),
                  duration: 60,
                }})
                document.querySelector(\'#conference-deadline\').appendChild(conferenceDeadlineCalendar);

                // render countdown timer
                $(\'#conf-timer\').countdown(confDeadline.toDate(), function(event) {{
                  $(this).html(event.strftime(\'%D days %Hh %Mm %Ss\'));
                }});
                $(\'.deadline-time\').html(confDeadline.toString());

                // convert deadline to local timezone
                try {{
                  var localConfDeadline = moment.tz(confDeadline, local_timezone);
                  $(\'.deadline-local-time\').html(localConfDeadline.toString());
                }}
                catch(err) {{
                  console.log("Error converting to local timezone.");
                }}
              }} else {{
                $(\'#conf-deadline-info\').hide();
                $(\'#conf-deadline-timer\').hide();
              }}
            }}''')
    
    return '\n'.join(js_lines)

def generate_conference_page():
    """Generate the conference detail page."""
    conferences = load_conferences()
    
    # Generate JavaScript data
    conference_js = generate_conference_js_data(conferences)
    
    # Read the template
    with open('conference/index.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Find the position to insert the conference data
    # Look for the line that starts the conference processing
    lines = template.split('\n')
    start_line = -1
    end_line = -1
    
    for i, line in enumerate(lines):
        if 'if (conf == "neurips24")' in line:
            start_line = i
        elif start_line != -1 and line.strip() == '}' and i > start_line:
            # Find the end of the conference processing block
            end_line = i
            break
    
    if start_line != -1 and end_line != -1:
        # Replace the hardcoded conference data with dynamic data
        new_lines = lines[:start_line] + [conference_js] + lines[end_line+1:]
        final_html = '\n'.join(new_lines)
    else:
        # If we can't find the exact location, append to the end before the closing script tag
        script_end = template.rfind('</script>')
        if script_end != -1:
            final_html = template[:script_end] + conference_js + '\n    ' + template[script_end:]
        else:
            # Fallback: append to the end
            final_html = template + '\n    <script>\n' + conference_js + '\n    </script>'
    
    # Write the updated conference page
    with open('conference/index.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Generated conference detail page with {len(conferences)} conferences")

def main():
    """Main function."""
    print("Generating conference detail pages from conferences.yml...")
    generate_conference_page()
    print("Conference detail page generation complete!")

if __name__ == "__main__":
    main()
