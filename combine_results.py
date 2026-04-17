"""
combine_results.py — Merge all extracted JSON files into year-based Excel + CSV.

Usage:
  python combine_results.py

Reads all .json files from output_json/ and produces:
  - data/<year>/all_schools_summary.xlsx
  - data/<year>/all_schools_flat.csv
"""

import json
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    raise ImportError("Run: pip install pandas openpyxl")


OUTPUT_DIR = Path("output_json")
DATA_YEAR = "2026"
DATA_DIR = Path("data") / DATA_YEAR
EXCEL_OUT = DATA_DIR / "all_schools_summary.xlsx"
CSV_OUT = DATA_DIR / "all_schools_flat.csv"


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Recursively flatten a nested dict. Skip arrays."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        elif isinstance(v, list):
            pass  # Arrays handled separately
        else:
            items[new_key] = v
    return items


def extract_salary_rows(data: dict, school_name: str, section_key: str) -> list[dict]:
    """Extract rows from an array section (salary by occupation/industry/region)."""
    rows = []
    items = data.get(section_key, [])
    if not isinstance(items, list):
        return rows
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {"school": school_name}
        row.update(item)
        rows.append(row)
    return rows


def extract_specialty_rankings(data: dict, school_name: str) -> list[dict]:
    """Extract specialty ranking rows."""
    rows = []
    items = data.get("specialty_rankings", [])
    if not isinstance(items, list):
        return rows
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {"school": school_name}
        row.update(item)
        rows.append(row)
    return rows


def extract_countries(data: dict, school_name: str) -> list[dict]:
    """Extract countries most represented."""
    rows = []
    countries = data.get("student_body_all_programs", {}).get(
        "countries_most_represented", []
    )
    if not isinstance(countries, list):
        return rows
    for item in countries:
        if not isinstance(item, dict):
            continue
        row = {"school": school_name}
        row.update(item)
        rows.append(row)
    return rows


def main():
    json_files = sorted(OUTPUT_DIR.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {OUTPUT_DIR}/")
        return

    print(f"Found {len(json_files)} JSON files")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Collect data
    flat_rows = []
    salary_by_occupation_rows = []
    salary_by_industry_rows = []
    salary_by_region_rows = []
    specialty_ranking_rows = []
    country_rows = []

    for jf in json_files:
        school_key = jf.stem
        print(f"  Reading: {jf.name}")

        with open(jf, encoding="utf-8") as f:
            data = json.load(f)

        # Skip error files
        if "_error" in data:
            print(f"    [!] Skipping; extraction had errors")
            continue

        school_label = data.get("school_info", {}).get(
            "business_school_name", school_key
        )

        # Flat summary
        flat = flatten_dict(data)
        flat["_file"] = jf.name
        flat_rows.append(flat)

        # Array sections
        salary_by_occupation_rows.extend(
            extract_salary_rows(data, school_label, "base_salary_by_occupation")
        )
        salary_by_industry_rows.extend(
            extract_salary_rows(data, school_label, "base_salary_by_industry")
        )
        salary_by_region_rows.extend(
            extract_salary_rows(data, school_label, "base_salary_by_geographic_region")
        )
        specialty_ranking_rows.extend(extract_specialty_rankings(data, school_label))
        country_rows.extend(extract_countries(data, school_label))

    # Build DataFrames
    df_flat = pd.DataFrame(flat_rows)
    df_occ = (
        pd.DataFrame(salary_by_occupation_rows)
        if salary_by_occupation_rows
        else pd.DataFrame()
    )
    df_ind = (
        pd.DataFrame(salary_by_industry_rows)
        if salary_by_industry_rows
        else pd.DataFrame()
    )
    df_reg = (
        pd.DataFrame(salary_by_region_rows) if salary_by_region_rows else pd.DataFrame()
    )
    df_spec = (
        pd.DataFrame(specialty_ranking_rows)
        if specialty_ranking_rows
        else pd.DataFrame()
    )
    df_countries = pd.DataFrame(country_rows) if country_rows else pd.DataFrame()

    # Save CSV (flat only)
    df_flat.to_csv(CSV_OUT, index=False, encoding="utf-8")
    print(
        f"\n[OK] Flat CSV: {CSV_OUT} ({len(df_flat)} rows x {len(df_flat.columns)} columns)"
    )

    # Save Excel (multi-sheet)
    with pd.ExcelWriter(EXCEL_OUT, engine="openpyxl") as writer:
        df_flat.to_excel(writer, sheet_name="Summary", index=False)

        if not df_occ.empty:
            df_occ.to_excel(writer, sheet_name="Salary by Occupation", index=False)
        if not df_ind.empty:
            df_ind.to_excel(writer, sheet_name="Salary by Industry", index=False)
        if not df_reg.empty:
            df_reg.to_excel(writer, sheet_name="Salary by Region", index=False)
        if not df_spec.empty:
            df_spec.to_excel(writer, sheet_name="Specialty Rankings", index=False)
        if not df_countries.empty:
            df_countries.to_excel(writer, sheet_name="Intl Students", index=False)

    sheet_count = 1 + sum(
        [
            not df_occ.empty,
            not df_ind.empty,
            not df_reg.empty,
            not df_spec.empty,
            not df_countries.empty,
        ]
    )
    print(f"[OK] Excel: {EXCEL_OUT} ({sheet_count} sheets)")

    # Print quick comparison table
    if "school_info.business_school_name" in df_flat.columns:
        compare_cols = [
            "school_info.business_school_name",
            "school_info.us_news_rank",
            "school_info.us_news_overall_score",
            "admissions_and_enrollment.acceptance_rate",
            "base_salary_overall.average_base_salary",
            "ranking_scores_two_year_averages.peer_assessment_score_out_of_5",
        ]
        available = [c for c in compare_cols if c in df_flat.columns]
        if available:
            print(f"\n{'=' * 80}")
            print("Quick Comparison:")
            print(f"{'=' * 80}")
            print(df_flat[available].to_string(index=False))

    print(f"\nDone! Files saved:")
    print(f"  {EXCEL_OUT.resolve()}")
    print(f"  {CSV_OUT.resolve()}")


if __name__ == "__main__":
    main()
