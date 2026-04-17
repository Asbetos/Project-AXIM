# Project AXIM  (AI eXtraction for Institutional Metrics)

The primary scope of this project is to extract all institutional metrics from the US News website using semantic parsing through Claude API.

## Overview
US News MBA Data Extraction — Automation Guide

There are 3 approaches, ordered from simplest to most automated:

| Approach | Effort | Reliability | Speed (50 schools) | Prerequisites |
|----------|--------|-------------|---------------------|---------------|
| **1. Batch Text Files** | Medium (manual copy-paste) | Highest | ~2 hours | Anthropic API key |
| **2. Playwright Browser Bot** | Low (fully automated) | Medium (can break if site changes) | ~30 min | API key + US News premium login |
| **3. Hybrid Clipboard** | Low per school | High | ~1 hour | API key |

**Recommendation**: Start with **Approach 1** to validate everything works, then move to **Approach 2** if you need to scale to many schools.

---

## Setup (all approaches)

```bash
# 1. Create a project folder
mkdir usnews_mba_scraper && cd usnews_mba_scraper

# 2. Install dependencies
pip install anthropic playwright pandas openpyxl

# 3. Install Playwright browsers (only needed for Approach 2)
playwright install chromium

# 4. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 5. Place the extraction prompt file
# Copy usnews_mba_extraction_prompt.md into this folder
```

---

## Approach 1: Batch Text Files (Recommended Start)

**How it works:**
1. You manually open each school's US News page in your browser
2. Expand all sections, Ctrl+A → Ctrl+C → paste into a .txt file
3. Run `extract_batch.py` — it reads all .txt files and outputs JSON

**Steps:**
1. Create a folder called `page_texts/`
2. For each school, save the copied text as `school_name.txt` (e.g., `wharton.txt`, `stanford_gsb.txt`)
3. Run: `python extract_batch.py`
4. Output appears in `output_json/` folder + a combined `all_schools.xlsx`

---

## Approach 2: Playwright Browser Bot (Fully Automated)

**How it works:**
1. Script opens a real browser, logs into US News premium
2. Navigates to each school URL from a list
3. Expands all collapsible sections automatically
4. Extracts visible text
5. Sends to Claude API and saves JSON

**Steps:**
1. Fill in `schools.csv` with school names and URLs
2. Set your US News login credentials in `.env`
3. Run: `python scrape_and_extract.py`
4. Output in `output_json/` folder

**⚠️ Important:** Respect US News' terms of service. Use reasonable delays between requests. This is for personal research/academic use of data you have premium access to.

---

## Approach 3: Hybrid Clipboard (Quick per-school)

**How it works:**
1. You copy a school's page text to clipboard
2. Run `python extract_clipboard.py`
3. It reads your clipboard, sends to Claude, saves JSON

Good for doing a few schools at a time without creating files.

---

## File Structure

```
usnews_mba_scraper/
├── extraction_prompt.md          # The prompt template (already created)
├── schools.csv                   # List of school URLs (for Approach 2)
├── .env                          # API keys and credentials
├── extract_batch.py              # Approach 1: batch text files
├── scrape_and_extract.py         # Approach 2: Playwright automation
├── extract_clipboard.py          # Approach 3: clipboard
├── combine_results.py            # Merge all JSONs into Excel/CSV
├── page_texts/                   # Input: pasted text files
│   ├── wharton.txt
│   ├── stanford_gsb.txt
│   └── ...
└── output_json/                  # Output: extracted JSON files
    ├── wharton.json
    ├── stanford_gsb.json
    └── ...
```
