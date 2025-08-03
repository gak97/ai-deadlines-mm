# AI‑Powered Conference Discovery System

This system automatically discovers new AI conferences by combining web
scraping with AI analysis to find, categorise and validate conference
information.  It is based on the original implementation from the
Hugging Face `ai‑conference‑deadlines` project but has been adapted
to use Google's **Gemini** API instead of OpenAI's GPT models.

## Overview

The discovery pipeline works in multiple stages:

1. **Web scraping** – Searches multiple public sources (e.g. WikiCFP,
   deadline aggregators) for potential conferences.
2. **AI analysis** – Uses a large language model (LLM) to classify
   and extract structured data from the unstructured conference
   descriptions.
3. **Validation** – Filters results based on confidence scores and
   simple heuristics to avoid low‑quality or duplicate entries.
4. **Integration** – Adds validated conferences to your
   `conferences.yml` file.

## Configuration

### Environment variables

Set up the following environment variable in your GitHub repository
secrets:

* `GEMINI_API_KEY` – Your Gemini API key for AI analysis (optional but
  recommended).  If this is not set the AI enhancement step will be
  skipped and only basic scraping will run.

### Configuration file

Edit `.github/scripts/ai_config.yml` to customise the behaviour:

#### Target categories

```yaml
target_categories:
  machine-learning:
    - "machine learning"
    - "ML"
    - "artificial intelligence"
    # Add more keywords…
```

#### Discovery sources

```yaml
sources:
  wikicfp:
    enabled: true
    max_results_per_keyword: 10
  deadline_trackers:
    enabled: true
    urls:
      - "https://aideadlin.es/"
```
```

#### AI enhancement

```yaml
ai_enhancement:
  enabled: true
  model: "gemini-2.5-flash"
  confidence_threshold: 0.6
```

## How it works

### 1. Web scraping sources

* **WikiCFP (Call for Papers)** – Searches for conferences using your
  target keywords, extracts titles, deadlines and locations, then
  follows links to get more details.
* **Deadline tracking sites** – Scrapes popular AI deadline
  aggregators, identifies conferences with relevant keywords and
  collects their metadata.
* **University pages (optional)** – Can monitor AI department news
  pages for announcements, but this is disabled by default as it is
  resource‑intensive.

### 2. AI analysis

When a `GEMINI_API_KEY` is provided the system:

* **Categorises** conferences into your target categories.
* **Extracts** structured data (full names, locations, etc.).
* **Validates** that conferences are legitimate academic events.
* **Assigns confidence scores** based on relevance and quality.

### 3. Filtering & validation

Conferences must meet several criteria before being added:

* **Confidence score** ≥ 0.6 (configurable)
* **Title length** ≥ 3 characters
* **Has relevant tags** from your target categories
* **Future dates** (current or next year)
* **Not duplicates** of existing conferences

### 4. Output

Valid conferences are:

* Added to `src/data/conferences.yml` (falling back to
  `_data/conferences.yml` when the `src/data` directory is missing).
* Formatted consistently with existing entries.
* Marked with the discovery source for verification.
* Sorted by deadline to maintain a clean file.

## Usage

### Automatic (recommended)

The discovery process is wired up to run automatically via GitHub
Actions:

* **Weekly** – Every Monday at 6 AM UTC the workflow scrapes
  conferences, runs AI classification and commits any changes.
* **Manual** – You can trigger it via the GitHub Actions “Run
  workflow” button.
* **On changes** – When someone modifies `conferences.yml` the AI
  discovery will run during the PR checks to catch new events.

### Manual execution

You can also run the script locally to test it:

```bash
# Install dependencies
pip install -r .github/scripts/requirements.txt

# Set API key (optional)
export GEMINI_API_KEY="your-api-key-here"

# Run discovery
python .github/scripts/ai_conference_discovery.py
```

## Sample output

When the system finds a new conference it will add an entry similar to
this:

```yaml
- title: NEURIPS
  year: 2026
  id: neurips26
  full_name: Conference on Neural Information Processing Systems
  link: https://neurips.cc/Conferences/2026
  deadline: '2026-05-20 23:59:59'
  timezone: AoE
  tags:
    - machine-learning
    - deep-learning
  city: Vancouver
  country: Canada
  note: 'Auto‑discovered from WikiCFP. Please verify details.'
```

## Monitoring & debugging

### Logs

The script prints progress messages as it runs so you can follow the
scraping process, AI analysis results, filtering decisions and any
errors or warnings.

### Manual review

All auto‑discovered conferences include source attribution in the
`note` field.  If you run the script via a GitHub Action that
creates pull requests you can review the additions before merging.

### Troubleshooting

* **No conferences found** – Check that your keywords in
  `ai_config.yml` are appropriate and that the scraping sources are
  reachable.
* **Low confidence scores** – Adjust `confidence_threshold` in the
  configuration or fine‑tune your keywords.
* **API rate limits** – Increase the delays in the rate limiting
  settings or temporarily disable the AI enhancement by not
  providing a `GEMINI_API_KEY`.
* **Duplicates** – The system automatically deduplicates based on
  title and year, but manual review is always recommended.

## Customisation

### Adding new sources

1. Add URLs to the `sources` section in `ai_config.yml`.
2. Implement parsing logic in `ai_conference_discovery.py`.
3. Test with a small keyword set first to verify extraction.

### Modifying categories

To change the set of categories:

1. Edit `target_categories` in `ai_config.yml`.
2. Add relevant keywords for each category.
3. Update any category mapping logic in your filtering functions if
   needed.

### Adjusting quality filters

You can fine‑tune discovery by modifying:

* `confidence_threshold` – Higher values result in fewer but higher
  quality conferences.
* `years_ahead` – How far into the future to look.
* `exclude_patterns` – Patterns to filter out (e.g. "workshop").

## Cost considerations

### Gemini API usage

Costs for using the Gemini API are based on the amount of text
generated and may vary by region and plan.  Running one discovery
round typically analyses a few dozen candidates and should be
affordable.  You can disable the AI analysis entirely by setting
`ai_enhancement.enabled: false` in the configuration or by omitting
 the `GEMINI_API_KEY`.

### Rate limiting

The system respects rate limits for both the scraping sources and the
Gemini API.  You can adjust the delay and retry settings in
`ai_config.yml` to strike a balance between speed and politeness.
