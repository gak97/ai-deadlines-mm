# AI Conference Deadlines - Updates

## Summary of Changes

This update addresses three main issues:

1. **Fixed subject search filters** - Added proper subject tags to all conferences
2. **Enhanced conference information display** - Now shows all available information including abstract deadlines and notes
3. **Added missing conferences** - Included ICWSM and LREC conferences
4. **Fixed Jekyll build process** - Added proper Jekyll configuration for deployment

## Changes Made

### 1. Conference Data Updates (`_data/conferences.yml`)

- **Added subject tags** to all conferences:
  - `ML` - Machine Learning
  - `CV` - Computer Vision
  - `CG` - Computer Graphics
  - `NLP` - Natural Language Processing
  - `RO` - Robotics
  - `SP` - Speech/Signal Processing
  - `DM` - Data Mining
  - `AP` - Automated Planning
  - `KR` - Knowledge Representation
  - `HCI` - Human-Computer Interaction

- **Added notes** for conferences with abstract deadlines or special submission requirements
- **Added ICWSM 2025** (International Conference on Web and Social Media)
- **Added LREC 2025** (International Conference on Language Resources and Evaluation)

### 2. HTML Generation System

Created a new HTML generation system (`generate_html.py`) that:

- Reads conference data from `_data/conferences.yml`
- Generates proper HTML with subject tags for filtering
- Includes all conference information (dates, locations, notes, abstract deadlines)
- Adds JavaScript for deadline processing and countdown timers
- Ensures proper CSS classes for subject filtering

### 3. CSS Styling Updates (`static/css/deadlines.css`)

- Enhanced styling for subject tags (`.conf-sub`)
- Improved note styling (`.note`)
- Added styling for abstract deadlines (`.abstract-deadline`)
- Added responsive design for mobile devices
- Better visual hierarchy and spacing

### 4. Template System

- Created `index_template.html` as a base template
- Uses `{{CONFERENCES}}` placeholder for dynamic content
- Includes all necessary JavaScript and CSS references

### 5. Jekyll Configuration

- **Gemfile**: Added Jekyll dependencies and configuration
- **_config.yml**: Jekyll site configuration with proper exclusions
- **Build Process**: `bundle exec jekyll build --baseurl "/ai-deadlines-mm"` now works correctly
- **Cross-Platform Support**: Updated `Gemfile.lock` to support both Windows (`x64-mingw-ucrt`) and Linux (`x86_64-linux`) platforms

The Jekyll build process:
1. Installs dependencies with `bundle install`
2. Builds the site with `bundle exec jekyll build --baseurl "/ai-deadlines-mm"`
3. Generates the `_site` directory with all static assets
4. Excludes development files (Python scripts, templates) from the build
5. Works on both local Windows development and GitHub Actions Linux environments

## How to Use

### Regenerating the Website

To update the website with new conference data:

```bash
python generate_html.py
```

This will:
1. Read the latest conference data from `_data/conferences.yml`
2. Generate the complete `index.html` file
3. Include all necessary JavaScript for functionality

### Adding New Conferences

1. Add conference data to `_data/conferences.yml` with proper tags
2. Run `python generate_html.py` to regenerate the HTML
3. The new conference will automatically appear with proper filtering

### Subject Filtering

The subject filter now works correctly:
- Click on subject tags to filter by that subject
- Use the dropdown to select multiple subjects
- All conferences with matching tags will be displayed

## File Structure

```
├── _data/
│   └── conferences.yml          # Conference data with tags
├── static/css/
│   └── deadlines.css            # Updated styling
├── generate_html.py             # HTML generation script
├── index_template.html          # HTML template
├── index.html                   # Generated main page
└── UPDATES.md                   # This file
```

## Technical Details

### Subject Tag System

Each conference now has a `tags` array with appropriate subject codes:
```yaml
- id: icml25
  title: ICML
  tags: [ML]  # Machine Learning
  # ... other fields
```

### HTML Structure

Generated conference HTML includes:
- Proper CSS classes for filtering (e.g., `ml-conf`, `cv-conf`)
- Subject tags with click handlers
- Notes and abstract deadline information
- All conference metadata

### JavaScript Integration

The generated HTML includes JavaScript that:
- Processes deadlines and timezones
- Creates countdown timers
- Handles subject filtering
- Manages past/upcoming conference sorting

## Future Improvements

- Add more subject categories as needed
- Enhance mobile responsiveness
- Add conference search functionality
- Implement conference recommendations
- Add conference impact metrics (h-index, etc.)
