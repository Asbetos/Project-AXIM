"""
extract_clipboard.py — Approach 3: Clipboard-based extraction

Usage:
  1. Open a school's US News page, expand all sections
  2. Ctrl+A → Ctrl+C (copy all text)
  3. Run:  python extract_clipboard.py school_name
  4. JSON saved to output_json/school_name.json

Example:
  python extract_clipboard.py wharton
  python extract_clipboard.py stanford_gsb
  python extract_clipboard.py mit_sloan
"""

import sys
import time
from pathlib import Path

try:
    import pyperclip
except ImportError:
    raise ImportError(
        "Run: pip install pyperclip\n"
        "On Linux you may also need: sudo apt install xclip"
    )

from core_extractor import load_prompt, extract_school_data, save_json


OUTPUT_DIR = Path("output_json")
PAGE_TEXTS_DIR = Path("page_texts")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_clipboard.py <school_name>")
        print("Example: python extract_clipboard.py wharton")
        print("\nSteps:")
        print("  1. Open the school page in your browser")
        print("  2. Expand ALL sections (SEE MORE buttons)")
        print("  3. Ctrl+A → Ctrl+C to copy all text")
        print("  4. Run this script with a name for the school")
        sys.exit(1)

    school_name = sys.argv[1].strip().lower().replace(" ", "_")

    # Read clipboard
    print("Reading clipboard...")
    page_text = pyperclip.paste()

    if not page_text or len(page_text.strip()) < 500:
        print("✗ Clipboard is empty or too short.")
        print("  Make sure you copied the full page text (Ctrl+A → Ctrl+C)")
        sys.exit(1)

    print(f"✓ Got {len(page_text):,} characters from clipboard")

    # Save raw text backup
    PAGE_TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    txt_path = PAGE_TEXTS_DIR / f"{school_name}.txt"
    txt_path.write_text(page_text, encoding="utf-8")
    print(f"✓ Saved raw text: {txt_path}")

    # Load prompt
    prompt = load_prompt()

    # Extract
    print("Sending to Claude API...")
    start = time.time()
    data = extract_school_data(page_text=page_text, prompt_text=prompt)
    elapsed = time.time() - start
    print(f"✓ Extraction took {elapsed:.1f}s")

    # Save JSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{school_name}.json"
    save_json(data, output_path)

    # Quick summary
    if "school_info" in data:
        info = data["school_info"]
        print(f"\n  School: {info.get('school_name', '?')} ({info.get('business_school_name', '?')})")
        print(f"  Rank: #{info.get('us_news_rank', '?')}")
        print(f"  Score: {info.get('us_news_overall_score', '?')}")

    print(f"\nDone! JSON saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
