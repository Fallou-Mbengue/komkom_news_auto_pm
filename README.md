# Komkom News — Deep Research Module

A web scraping system for structured opportunity data, powered by Scrapy and PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Make (for workflows)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Set these variables (e.g. in `.env` file or your shell):

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Running the Crawler

```bash
make migrate
make crawl
```

## Running Tests

```bash
make test
```

## Adding a New Source

Edit `deep_research/config/sources.yaml` and add a dictionary entry following the existing pattern:

```yaml
- id: "mysource"
  name: "My Source"
  start_urls:
    - "https://example.com/opportunities"
  list_selector: "div.item"
  title_selector: "h2::text"
  description_selector: "p.desc::text"
  link_selector: "a.more::attr(href)"
  date_selector: "span.date::text"
  type: "financement"  # or "accompagnement"
```

## Assumptions

- **Only static HTML pages supported initially**. For JavaScript-heavy sites, we will integrate Splash or Selenium in future.
- Data normalization is best-effort; sector/stage/amount extraction may be improved as we iterate.

---

## Running Wekomkom spider

The Wekomkom spider scrapes public opportunities from https://wekomkom.com/accompagnement.  
Selectors are hypothetical and may need adjustment after real deployment (see `deep_research/spiders/wekomkom_spider.py` and test header).

To run the spider:

```bash
scrapy crawl wekomkom
```

## Database migration required

**Note:** Two new columns are added to the opportunities table:  
- `eligibility_criteria` (Text, nullable)
- `publication_date` (Date, nullable)

Existing users:  
You must run the migration to update your DB schema:
```bash
make migrate
```