"""extract_batch.py — Parallel batch extraction using Claude Sonnet 4.6.

Reads page_texts/*.txt, sends each to Claude API concurrently, and saves all results.

Usage:
    python extract_batch.py              # Claude Sonnet 4.6 (default)
    python extract_batch.py --workers 8  # 8 concurrent API calls
    python extract_batch.py --retry-failed  # Re-process only failed schools

Output:
    all_schools.json — JSON array of all school objects
    output_json/ — Individual JSON backups (checkpoint on re-run)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import anthropic

from core_extractor import MAX_TOKENS, PROMPT_FILE, load_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"

INPUT_DIR = Path("page_texts")
OUTPUT_DIR = Path("output_json")
COMBINED_FILE = Path("all_schools.json")

DEFAULT_WORKERS = 5


def process_school(
    txt_path: Path, prompt: str, model: str
) -> tuple[str, dict | None, str | None]:
    """Extract one school. Returns (stem, data, error)."""
    stem = txt_path.stem
    page_text = txt_path.read_text(encoding="utf-8")

    if len(page_text.strip()) < 500:
        return stem, None, f"file too short ({len(page_text)} chars)"

    user_message = f"<page_content>\n{page_text}\n</page_content>\n\n{prompt}"

    for attempt in range(1, 6):
        try:
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                temperature=0,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = resp.content[0].text.strip()

            raw = _strip_fences(raw)
            data = json.loads(raw)
            data["_source_file"] = stem
            return stem, data, None

        except json.JSONDecodeError as e:
            if attempt < 5:
                time.sleep(2)
                continue
            return stem, None, f"JSON parse error: {e}"

        except anthropic.RateLimitError:
            time.sleep(30 * attempt)
            continue

        except anthropic.APIError as e:
            if attempt < 5:
                time.sleep(5)
                continue
            return stem, None, f"API error: {e}"

        except Exception as e:
            if attempt < 5:
                time.sleep(5)
                continue
            return stem, None, f"Error: {e}"

    return stem, None, "max retries exceeded"


def _strip_fences(text: str) -> str:
    """Remove markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def _clean(data: dict) -> dict:
    """Remove internal keys (prefixed with _) before saving."""
    return {k: v for k, v in data.items() if not k.startswith("_")}


def save_combined(results: list[dict], path: Path):
    """Save the combined JSON array."""
    clean = [_clean(r) for r in results]
    path.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")


def save_individual(data: dict, output_dir: Path):
    """Save one school's JSON as a backup."""
    stem = data.get("_source_file", "unknown")
    path = output_dir / f"{stem}.json"
    path.write_text(
        json.dumps(_clean(data), indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Batch extract school data using Claude Sonnet 4.6"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Concurrent API calls (default: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-process only schools without successful output",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Check your .env file.")
        sys.exit(1)

    prompt_path = Path(PROMPT_FILE)
    if not prompt_path.exists():
        print(f"Prompt file not found: {PROMPT_FILE}")
        sys.exit(1)
    prompt = prompt_path.read_text(encoding="utf-8")
    print(f"Loaded prompt: {PROMPT_FILE} ({len(prompt):,} chars)")

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_files = sorted(INPUT_DIR.glob("*.txt"))

    if not all_files:
        print(f"No .txt files in {INPUT_DIR}/")
        return

    done: set[str] = set()
    results: list[dict] = []
    for jf in OUTPUT_DIR.glob("*.json"):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if "_error" not in data and "school_info" in data:
                data["_source_file"] = jf.stem
                results.append(data)
                done.add(jf.stem)
        except Exception:
            pass

    remaining = [f for f in all_files if f.stem not in done]

    if args.retry_failed:
        print(
            f"--retry-failed: re-processing {len(remaining)} school(s) without output"
        )

    print(f"\n{'=' * 60}")
    print(f"Model: {args.model}")
    print(f"Total schools: {len(all_files)}")
    print(f"Already done: {len(done)}")
    print(f"Remaining: {len(remaining)}")
    print(f"Workers: {args.workers}")
    print(f"Est. cost: ~${len(remaining) * 0.02:.2f}")
    print(f"{'=' * 60}\n")

    if not remaining:
        save_combined(results, COMBINED_FILE)
        print(f"All schools already extracted!")
        print(f"Saved {COMBINED_FILE} ({len(results)} schools)")
        return

    completed = 0
    failed = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_school, f, prompt, args.model): f.stem
            for f in remaining
        }

        for future in as_completed(futures):
            stem = futures[future]
            try:
                _, data, error = future.result()
            except Exception as e:
                failed.append((stem, str(e)))
                continue

            if error:
                failed.append((stem, error))
                print(f" [X] {stem}: {error}")
                continue

            results.append(data)
            save_individual(data, OUTPUT_DIR)
            completed += 1

            info = data.get("school_info", {})
            school = info.get("business_school_name") or stem
            rank = info.get("us_news_rank", "?")
            print(f" [OK] [{completed}/{len(remaining)}] {school} (#{rank})")

    elapsed = time.time() - start_time

    save_combined(results, COMBINED_FILE)

    print(f"\n{'=' * 60}")
    print("EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"New: {completed} school(s)")
    print(f"Previous: {len(done)} school(s)")
    print(f"Total: {len(results)} / {len(all_files)} school(s)")
    print(f"Time: {elapsed:.0f}s")

    if failed:
        print(f"Failed: {len(failed)}")
        for name, err in failed:
            print(f" - {name}: {err}")

    print(f"\nOutput: {COMBINED_FILE.resolve()}")
    print(f"Backup: {OUTPUT_DIR.resolve()}")

    if len(results) == len(all_files):
        print(f"\n[OK] All {len(results)} schools extracted!")

    print(f"\nLoad in pandas:")
    print(f" import pandas as pd")
    print(
        f" df = pd.json_normalize(pd.read_json('{COMBINED_FILE}').to_dict('records'))"
    )


if __name__ == "__main__":
    main()
