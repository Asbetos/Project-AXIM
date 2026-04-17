"""Audit extracted JSON fields against source text files."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
JSON_DIR = ROOT / "output_json"
TEXT_DIR = ROOT / "page_texts"
REPORT_PATH = ROOT / "audit_report.json"
SUMMARY_PATH = ROOT / "audit_summary.json"

MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


@dataclass
class TextViews:
    raw: str
    lower: str
    normalized: str
    compact: str
    digits: str


def build_text_views(text: str) -> TextViews:
    normalized = normalize_text(text)
    compact = compact_text(text)
    digits = re.sub(r"\D+", "", text)
    return TextViews(
        raw=text,
        lower=text.lower(),
        normalized=normalized,
        compact=compact,
        digits=digits,
    )


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            items.extend(flatten(value, new_prefix))
        return items
    if isinstance(obj, list):
        for index, value in enumerate(obj):
            new_prefix = f"{prefix}[{index}]"
            items.extend(flatten(value, new_prefix))
        return items
    items.append((prefix, obj))
    return items


def regex_search(candidate: str, text: str) -> bool:
    if not candidate:
        return False
    if candidate[0].isalnum() and candidate[-1].isalnum():
        pattern = rf"(?<![A-Za-z0-9]){re.escape(candidate)}(?![A-Za-z0-9])"
        return re.search(pattern, text) is not None
    return candidate in text


def month_variants(value: str) -> list[str]:
    m = re.fullmatch(r"([A-Za-z]{3})\.?\s+(\d{1,2})", value.strip())
    if not m:
        return []
    mon = MONTHS.get(m.group(1).lower())
    day = int(m.group(2))
    if not mon:
        return []
    return [f"{mon:02d}/{day:02d}", f"{mon}/{day}", f"{m.group(1).lower()} {day:02d}"]


def slash_date_variants(value: str) -> list[str]:
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", value.strip())
    if not m:
        return []
    mon = int(m.group(1))
    day = int(m.group(2))
    month_name = datetime(2000, mon, 1).strftime("%b").lower()
    return [
        f"{month_name}. {day:02d}",
        f"{month_name}. {day}",
        f"{month_name} {day:02d}",
    ]


def numeric_candidates(value: Any) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    if isinstance(value, bool):
        return [(str(value).lower(), "exact")]
    if isinstance(value, int):
        candidates.extend(
            [
                (str(value), "exact"),
                (f"{value:,}", "formatted"),
                (f"${value:,}", "currency"),
                (f"#{value}", "rank"),
            ]
        )
        return candidates

    if isinstance(value, float):
        raw = f"{value}"
        raw = raw.rstrip("0").rstrip(".") if "." in raw else raw
        candidates.append((raw, "exact"))

        if 0 <= value <= 1:
            percent = value * 100
            for digits in range(0, 4):
                formatted = f"{percent:.{digits}f}".rstrip("0").rstrip(".")
                if formatted:
                    candidates.append((f"{formatted}%", "percent"))
                    candidates.append((formatted, "percent_plain"))
        return dedupe_candidates(candidates)

    return candidates


def string_candidates(value: str) -> list[tuple[str, str]]:
    value = value.strip()
    if not value:
        return []

    candidates: list[tuple[str, str]] = [(value.lower(), "exact")]
    compact = compact_text(value)
    if compact:
        candidates.append((compact, "compact"))

    if value == "NA":
        candidates.extend(
            [
                ("n/a", "na_token"),
                ("a/v", "na_token"),
                ("na", "na_token"),
                ("not available", "na_token"),
            ]
        )

    digits = re.sub(r"\D+", "", value)
    if len(digits) >= 7:
        candidates.append((digits, "digits"))

    candidates.extend((item, "date_variant") for item in month_variants(value))
    candidates.extend((item, "date_variant") for item in slash_date_variants(value))
    return dedupe_candidates(candidates)


def dedupe_candidates(candidates: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for candidate, kind in candidates:
        key = candidate.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append((key, kind))
    return deduped


def validate_value(path: str, value: Any, text: TextViews) -> dict[str, Any]:
    if isinstance(value, str):
        candidates = string_candidates(value)
    elif isinstance(value, (int, float, bool)):
        candidates = numeric_candidates(value)
    else:
        return {
            "path": path,
            "value": value,
            "supported": False,
            "match_type": "unsupported_type",
        }

    for candidate, kind in candidates:
        target = text.lower
        if kind in {"compact", "digits"}:
            target = text.compact if kind == "compact" else text.digits
            if candidate in target:
                return {
                    "path": path,
                    "value": value,
                    "supported": True,
                    "match_type": kind,
                    "matched_candidate": candidate,
                }
            continue

        if regex_search(candidate, target):
            return {
                "path": path,
                "value": value,
                "supported": True,
                "match_type": kind,
                "matched_candidate": candidate,
            }

    return {
        "path": path,
        "value": value,
        "supported": False,
        "match_type": "unsupported",
    }


def audit_school(json_path: Path, txt_path: Path) -> dict[str, Any]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    text = build_text_views(txt_path.read_text(encoding="utf-8"))
    fields = flatten(data)

    supported = 0
    unsupported_items: list[dict[str, Any]] = []
    match_types: Counter[str] = Counter()

    for path, value in fields:
        result = validate_value(path, value, text)
        match_types[result["match_type"]] += 1
        if result["supported"]:
            supported += 1
        else:
            unsupported_items.append(result)

    return {
        "school": json_path.stem,
        "json_file": json_path.name,
        "text_file": txt_path.name,
        "total_fields": len(fields),
        "supported_fields": supported,
        "unsupported_fields": len(unsupported_items),
        "support_rate": round(supported / len(fields), 4) if fields else 0,
        "match_types": dict(match_types),
        "unsupported": unsupported_items,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit extracted JSON against text files"
    )
    parser.add_argument(
        "--schools",
        nargs="*",
        default=None,
        help="Optional list of school stems to audit",
    )
    parser.add_argument(
        "--report-path",
        default=str(REPORT_PATH),
        help="Path for full audit report output",
    )
    parser.add_argument(
        "--summary-path",
        default=str(SUMMARY_PATH),
        help="Path for audit summary output",
    )
    args = parser.parse_args()

    selected = set(args.schools or [])
    report_path = Path(args.report_path)
    summary_path = Path(args.summary_path)

    reports: list[dict[str, Any]] = []
    missing_text: list[str] = []

    for json_path in sorted(JSON_DIR.glob("*.json")):
        if selected and json_path.stem not in selected:
            continue
        txt_path = TEXT_DIR / f"{json_path.stem}.txt"
        if not txt_path.exists():
            missing_text.append(json_path.stem)
            continue
        reports.append(audit_school(json_path, txt_path))

    reports.sort(key=lambda item: (-item["unsupported_fields"], item["school"]))

    total_fields = sum(item["total_fields"] for item in reports)
    supported_fields = sum(item["supported_fields"] for item in reports)
    unsupported_fields = sum(item["unsupported_fields"] for item in reports)
    schools_with_issues = sum(1 for item in reports if item["unsupported_fields"] > 0)

    all_unsupported = []
    for item in reports:
        for problem in item["unsupported"]:
            all_unsupported.append(
                {
                    "school": item["school"],
                    "path": problem["path"],
                    "value": problem["value"],
                }
            )

    common_paths = Counter(problem["path"] for problem in all_unsupported).most_common(
        50
    )
    summary = {
        "schools_audited": len(reports),
        "schools_with_issues": schools_with_issues,
        "missing_text_files": missing_text,
        "total_fields": total_fields,
        "supported_fields": supported_fields,
        "unsupported_fields": unsupported_fields,
        "support_rate": round(supported_fields / total_fields, 4)
        if total_fields
        else 0,
        "most_common_unsupported_paths": common_paths,
        "top_10_worst_schools": [
            {
                "school": item["school"],
                "unsupported_fields": item["unsupported_fields"],
                "total_fields": item["total_fields"],
                "support_rate": item["support_rate"],
            }
            for item in reports[:10]
        ],
    }

    report_path.write_text(
        json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Schools audited: {summary['schools_audited']}")
    print(f"Total fields: {summary['total_fields']}")
    print(f"Supported fields: {summary['supported_fields']}")
    print(f"Unsupported fields: {summary['unsupported_fields']}")
    print(f"Support rate: {summary['support_rate']:.2%}")
    print(f"Schools with issues: {summary['schools_with_issues']}")
    print(f"Summary saved: {summary_path}")
    print(f"Full report saved: {report_path}")


if __name__ == "__main__":
    main()
