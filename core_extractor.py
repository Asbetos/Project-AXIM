"""
core_extractor.py — Shared extraction logic for all approaches.
Supports both Anthropic Claude and NVIDIA NIM (free) models.
"""

import os
import json
import time
from pathlib import Path
from typing import Literal

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None


# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
ProviderType = Literal["anthropic", "nvidia"]

DEFAULT_PROVIDER: ProviderType = "anthropic"
DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-6"
DEFAULT_MODEL_NVIDIA = "google/gemma-3-27b-it"

MAX_TOKENS = 16000
PROMPT_FILE = "extraction_prompt.md"

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


def load_prompt(prompt_path: str = PROMPT_FILE) -> str:
    """Load the extraction prompt from the markdown file."""
    path = Path(prompt_path)
    if not path.exists():
        path = Path(__file__).parent / prompt_path
        if not path.exists():
            raise FileNotFoundError(
                f"Extraction prompt not found at: {prompt_path}\n"
                f"Place 'usnews_mba_extraction_prompt.md' in the project folder "
                f"and rename it to 'extraction_prompt.md' (or update PROMPT_FILE)."
            )
    return path.read_text(encoding="utf-8")


def _get_nvidia_client():
    """Create OpenAI-compatible client for NVIDIA NIM."""
    if openai is None:
        raise ImportError("Run: pip install openai")
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable not set")
    return openai.OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)


def _get_anthropic_client():
    """Create Anthropic client."""
    if anthropic is None:
        raise ImportError("Run: pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic()


def extract_school_data(
    page_text: str,
    prompt_text: str | None = None,
    source_url: str = "",
    provider: ProviderType = DEFAULT_PROVIDER,
    model: str | None = None,
    max_retries: int = 3,
) -> dict:
    """
    Send page text to LLM and return the extracted JSON dict.

    Args:
        page_text: Plain text copied from the US News school profile page.
        prompt_text: The extraction prompt. Loaded from file if not provided.
        source_url: URL of the school page (written into metadata).
        provider: "anthropic" or "nvidia".
        model: Model to use. Defaults to best for each provider.
        max_retries: Retries on transient API errors.

    Returns:
        Parsed JSON dict with all school metrics.
    """
    if prompt_text is None:
        prompt_text = load_prompt()

    if model is None:
        model = (
            DEFAULT_MODEL_NVIDIA if provider == "nvidia" else DEFAULT_MODEL_ANTHROPIC
        )

    user_message = f"<page_content>\n{page_text}\n</page_content>\n\n{prompt_text}"

    if provider == "nvidia":
        return _extract_nvidia(user_message, model, source_url, max_retries)
    else:
        return _extract_anthropic(user_message, model, source_url, max_retries)


def _extract_nvidia(
    user_message: str, model: str, source_url: str, max_retries: int
) -> dict:
    """Extract using NVIDIA NIM API (OpenAI-compatible)."""
    client = _get_nvidia_client()

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": user_message}],
                temperature=0,
            )

            raw = response.choices[0].message.content.strip()
            raw = _strip_markdown_fences(raw)

            data = json.loads(raw)

            if "metadata" in data and source_url:
                data["metadata"]["source_url"] = source_url

            return data

        except json.JSONDecodeError as e:
            print(f" [!] JSON parse error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(" Retrying...")
                time.sleep(2)
            else:
                print(" [X] Failed to parse JSON after retries. Saving raw text.")
                return {"_raw_response": raw, "_error": str(e)}

        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "limit" in err_str:
                wait = 30 * attempt
                print(f" [!] Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f" [!] API error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    return {"_error": str(e)}

    return {"_error": "Max retries exceeded"}


def _extract_anthropic(
    user_message: str, model: str, source_url: str, max_retries: int
) -> dict:
    """Extract using Anthropic Claude API."""
    client = _get_anthropic_client()

    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": user_message}],
            )

            raw = response.content[0].text.strip()
            raw = _strip_markdown_fences(raw)

            data = json.loads(raw)

            if "metadata" in data and source_url:
                data["metadata"]["source_url"] = source_url

            return data

        except json.JSONDecodeError as e:
            print(f" [!] JSON parse error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(" Retrying...")
                time.sleep(2)
            else:
                print(" [X] Failed to parse JSON after retries. Saving raw text.")
                return {"_raw_response": raw, "_error": str(e)}

        except anthropic.RateLimitError:
            wait = 30 * attempt
            print(f" [!] Rate limited. Waiting {wait}s...")
            time.sleep(wait)

        except anthropic.APIError as e:
            print(f" [!] API error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(5)
            else:
                return {"_error": str(e)}

    return {"_error": "Max retries exceeded"}


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from model output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def save_json(data: dict, output_path: str | Path) -> None:
    """Write dict to a formatted JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f" [OK] Saved: {path}")
