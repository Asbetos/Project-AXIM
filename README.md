# US News MBA Data Extractor

This project automates collection and structuring of US News business school profile data.

It does three main jobs:
- discover the exact-number-ranked MBA schools from the US News rankings page
- scrape each school profile into a clean text snapshot
- send the text to Claude Sonnet and save structured JSON, CSV, and Excel outputs

The current refreshed dataset in this repo is based on the 2026 US News business school rankings.

## What The Repo Contains

- `scrape_and_extract.py`: discovers schools and scrapes each profile page into `page_texts/`
- `extract_batch.py`: sends the text files to Claude and creates one JSON file per school in `output_json/`
- `combine_results.py`: merges the JSON files into flat CSV and multi-sheet Excel outputs
- `core_extractor.py`: shared LLM extraction logic
- `extraction_prompt.md`: extraction instructions passed to the model
- `data/`: final exported datasets organized by ranking year

## Requirements

- Python 3.10+
- A US News premium account for the scraping step
- An Anthropic API key for the extraction step
- Google Chrome or Microsoft Edge installed locally

## Setup

1. Install Python dependencies.

```bash
pip install -r requirements.txt
```

2. Install the Playwright browser dependency.

```bash
playwright install chromium
```

3. Create your environment file from the template.

```bash
copy .env.example .env
```

4. Edit `.env` and set at least:

```env
ANTHROPIC_API_KEY=your_key_here
```

`NVIDIA_API_KEY` is optional and only needed if you switch back to the NVIDIA-based extraction path.

## End-To-End Run Guide

### Phase 1: Discover Ranked Schools

This refresh uses the exact-number-ranked schools only. The discovery step stops at the nominal-rank cutoff and writes the school list to `schools.csv`.

```bash
python scrape_and_extract.py --discover
```

Expected output:
- `schools.csv`
- 122 schools for the current 2026 rankings refresh

### Phase 2: Scrape The School Pages

This phase opens a real browser session, uses your logged-in US News premium access, expands page sections, and saves the raw text snapshots into `page_texts/`.

```bash
python scrape_and_extract.py --scrape-only
```

Notes:
- the script uses a persistent browser profile in `browser_profile/`
- rerunning is safe; already-scraped schools are skipped
- if the run is interrupted, run the same command again to resume

Expected output:
- one `.txt` file per school in `page_texts/`

### Phase 3: Extract Structured JSON With Claude Sonnet

This phase sends each `.txt` file to Claude Sonnet 4.6 with `temperature=0` and saves one JSON file per school.

```bash
python extract_batch.py --workers 20
```

Notes:
- `--workers 20` was used successfully for the refreshed 2026 dataset
- rerunning is safe; existing JSON files are skipped
- partial reruns work by deleting the JSONs you want to regenerate and rerunning the command

Expected output:
- per-school JSON files in `output_json/`
- combined JSON file `all_schools.json`

### Phase 4: Export Final CSV And Excel Deliverables

This phase flattens the per-school JSON files and writes the final deliverables into the year-specific data folder.

```bash
python combine_results.py
```

Expected output for the current refresh:
- `data/2026/all_schools_flat.csv`
- `data/2026/all_schools_summary.xlsx`

## Typical Full Refresh Sequence

Run the full pipeline in this order:

```bash
python scrape_and_extract.py --discover
python scrape_and_extract.py --scrape-only
python extract_batch.py --workers 20
python combine_results.py
```

## Output Layout

```text
data/
  2025/
    all_schools_flat.csv
    all_schools_summary.xlsx
  2026/
    all_schools_flat.csv
    all_schools_summary.xlsx
```

Transient working folders created during a run:
- `browser_profile/`
- `page_texts/`
- `output_json/`

These working folders are intentionally ignored by git.

## Notes On Validation

The repo includes an audit utility:

```bash
python audit_extractions.py
```

This validates extracted JSON fields against the scraped text files and writes:
- `audit_summary.json`
- `audit_report.json`

These audit artifacts are generated outputs and are ignored by git.

## Important Repo Hygiene

- do not commit `.env`
- do not commit browser session data in `browser_profile/`
- do not commit temporary scrape text or per-school JSON working files unless you explicitly want the intermediate artifacts in version control

## Current Refreshed Deliverables

The latest refreshed dataset in this repo is stored here:
- `data/2026/all_schools_flat.csv`
- `data/2026/all_schools_summary.xlsx`
