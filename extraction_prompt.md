# US News MBA School Metrics Extraction Prompt

---

## System / Instruction Prompt

You are a precise data-extraction agent. Your task is to extract **every available metric** from a US News Best Business Schools profile page for an MBA program and return the result as a single, valid JSON object.

---

## Rules

1. **Output format**: Return ONLY a valid JSON object — no markdown fences, no commentary, no preamble, no explanation. Just the raw JSON.

2. **Missing values**: If a data point is not present on the page or is listed as "N/A", set its value to `"NA"`.

3. **Numeric cleaning**:
   - Remove all currency symbols (`$`, `€`, etc.) and commas from numbers. Example: `$200,724` → `200724`
   - Convert all percentages to decimals. Example: `88.2%` → `0.882`, `20.5%` → `0.205`, `64%` → `0.64`, `0%` → `0.0`
   - Scores on a 1–5 scale (peer/recruiter assessment) remain as-is (e.g., `4.7`).
   - GMAT, GRE, TOEFL scores, counts of people, and rankings remain as plain integers (e.g., `740`, `165`, `1`).
   - GPA values remain as floats (e.g., `3.7`).
   - Work experience in months stays as an integer (e.g., `60`).
   - Application fees, tuition, salary, and bonus amounts are plain integers with no `$` or commas (e.g., `84830`).
   - Age stays as an integer (e.g., `28`).

4. **Text values**: School name, location, program names, concentration lists, and similar descriptive fields remain as strings.

5. **Arrays**: Where a field expects a list (e.g., specialty rankings, salary by occupation), return a JSON array of objects as shown in the template.

6. **Consistency**: Follow the key names in the template **exactly**. Do not rename, add, or remove keys.

7. **Two-year averages vs. single-year data**: The page reports BOTH two-year averages (in the Ranking Scores section) AND single-year figures (in the Career & Salary section). Extract both into their respective fields as labeled in the template.

8. **Yes/No fields**: Keep as strings: `"Yes"` or `"No"`.

---

## JSON Template

Fill every value below using data from the page. Replace each `"__"` placeholder with the extracted value or `"NA"` if unavailable.

```json
{
  "school_info": {
    "school_name": "__",
    "business_school_name": "__",
    "us_news_rank": "__",
    "us_news_rank_out_of": "__",
    "us_news_overall_score": "__",
    "city": "__",
    "state": "__",
    "zip_code": "__",
    "school_type": "__",
    "total_enrollment_all_programs": "__",
    "graduate_enrollment": "__",
    "total_enrollment": "__",
    "full_time_degree_seeking_percent": "__",
    "programs_offered": "__"
  },

  "tuition_and_fees": {
    "full_time_tuition_per_year_in_state": "__",
    "full_time_tuition_per_year_out_of_state": "__",
    "required_fees_full_time": "__",
    "required_fees_specialty_masters": "__",
    "tuition_and_fees_combined_in_state_out_of_state": "__",
    "food_housing_books_misc_full_time_mba": "__",
    "books_misc_expenses_specialty_masters": "__",
    "executive_mba_total_program_cost_in_state": "__",
    "executive_mba_total_program_cost_out_of_state": "__"
  },

  "financial_aid": {
    "financial_aid_available": "__",
    "financial_aid_director": "__",
    "financial_aid_phone": "__",
    "college_funded_aid_available": "__",
    "fellowships": "__",
    "teaching_assistantships": "__",
    "research_assistantships": "__",
    "international_students_eligible_for_college_funded_aid": "__"
  },

  "student_indebtedness_graduates": {
    "average_indebtedness_full_time_mba": "__",
    "percentage_with_debt_full_time_mba": "__",
    "average_indebtedness_specialty_masters": "__",
    "percentage_with_debt_specialty_masters": "__"
  },

  "application_info": {
    "application_fee": "__",
    "test_optional_admissions": "__",
    "us_application_deadline": "__",
    "application_deadlines_fulltime_us": "__",
    "application_deadlines_fulltime_international": "__",
    "admissions_process_description": "__",
    "director_of_admissions": "__",
    "fulltime_mba_phone": "__",
    "fulltime_mba_email": "__"
  },

  "admissions_and_enrollment": {
    "total_applicants": "__",
    "total_accepted_fulltime": "__",
    "total_enrolled_fulltime": "__",
    "acceptance_rate": "__",
    "average_age_of_new_entrants": "__",
    "students_with_prior_work_experience_count": "__",
    "average_work_experience_months": "__"
  },

  "gpa_data": {
    "percent_new_entrants_providing_gpa": "__",
    "average_undergraduate_gpa": "__",
    "undergraduate_gpa_range_10th_90th": "__"
  },

  "gmat_data": {
    "percent_new_entrants_providing_gmat_new": "__",
    "percent_new_entrants_providing_gmat_old": "__",
    "average_gmat_score_domestic": "__",
    "average_gmat_score_international": "__",
    "gmat_range_10th_90th": "__",
    "average_old_gmat_exam_score": "__"
  },

  "gre_data": {
    "gre_accepted_for_admissions": "__",
    "gre_accepted_as_alternative_to_gmat": "__",
    "percent_new_entrants_providing_gre": "__",
    "gre_score_range_10th_90th": "__"
  },

  "toefl_ielts_data": {
    "toefl_required_for_international_students": "__",
    "minimum_toefl_score_required": "__",
    "mean_toefl_entering_students": "__",
    "median_toefl_entering_students": "__",
    "minimum_ielts_score_required": "__"
  },

  "undergraduate_majors": {
    "business_and_commerce": "__",
    "humanities": "__",
    "engineering": "__",
    "science": "__",
    "economics": "__",
    "computer_science": "__",
    "law": "__",
    "social_science": "__",
    "other": "__"
  },

  "ranking_scores_two_year_averages": {
    "overall_score": "__",
    "fulltime_employed_at_graduation_two_yr_avg": "__",
    "fulltime_employed_3_months_after_two_yr_avg": "__",
    "avg_starting_salary_and_bonus_two_yr_avg": "__",
    "salaries_by_profession_indicator_rank": "__",
    "median_gmat_score_fulltime_new": "__",
    "median_gmat_score_fulltime_old": "__",
    "median_undergraduate_gpa": "__",
    "acceptance_rate": "__",
    "peer_assessment_score_out_of_5": "__",
    "recruiter_assessment_score_out_of_5": "__"
  },

  "student_body_all_programs": {
    "total_enrollment": "__",
    "countries_most_represented": [
      { "country": "__", "percent": "__" }
    ]
  },

  "student_body_fulltime_mba": {
    "enrollment": "__",
    "international_students_percent": "__",
    "female_percent": "__",
    "male_percent": "__",
    "other_gender_percent": "__",
    "race_ethnicity": {
      "international": "__",
      "white": "__",
      "asian": "__",
      "black": "__",
      "hispanic": "__",
      "two_or_more_races": "__",
      "unknown": "__",
      "american_indian": "__",
      "pacific_islander": "__"
    }
  },

  "career_and_salary_single_year": {
    "full_time_graduates": "__",
    "full_time_graduates_seeking_employment": "__",
    "employed_at_graduation_percent": "__",
    "employed_3_months_after_graduation_percent": "__"
  },

  "base_salary_overall": {
    "total_reporting_base_salary": "__",
    "low_base_salary": "__",
    "average_base_salary": "__",
    "high_base_salary": "__"
  },

  "base_salary_us_citizens": {
    "low_base_salary": "__",
    "average_base_salary": "__",
    "high_base_salary": "__"
  },

  "base_salary_foreign_nationals": {
    "low_base_salary": "__",
    "average_base_salary": "__",
    "high_base_salary": "__"
  },

  "signing_bonus_overall": {
    "total_reporting_signing_bonus": "__",
    "low_signing_bonus": "__",
    "average_signing_bonus": "__",
    "high_signing_bonus": "__"
  },

  "signing_bonus_us_citizens": {
    "low_signing_bonus": "__",
    "average_signing_bonus": "__",
    "high_signing_bonus": "__"
  },

  "signing_bonus_foreign_nationals": {
    "low_signing_bonus": "__",
    "average_signing_bonus": "__",
    "high_signing_bonus": "__"
  },

  "base_salary_by_occupation": [
    {
      "occupation": "Marketing / Sales",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Operations / Production",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "General Management",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Finance / Accounting",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Management Information Systems (MIS)",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Consulting",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Human Resources",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "occupation": "Other",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    }
  ],

  "base_salary_by_industry": [
    {
      "industry": "Consulting",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Consumer Products",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Financial Services",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Government",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Health Care",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Hospitality",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Manufacturing",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Media / Entertainment",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Non-profit",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Energy",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Real Estate",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Retail",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Technology",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Transportation & Logistics",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "industry": "Other",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    }
  ],

  "base_salary_by_geographic_region": [
    {
      "region": "Northeast",
      "states_included": "CT, MA, ME, NH, NJ, NY, RI, VT",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "Middle Atlantic",
      "states_included": "DC, DE, MD, PA, VA, WV",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "South",
      "states_included": "AL, AR, FL, GA, KY, LA, MS, NC, SC, TN",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "Midwest",
      "states_included": "IA, IL, IN, KS, MI, MN, MO, ND, NE, OH, SD, WI",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "Southwest",
      "states_included": "AZ, CO, NM, OK, TX",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "West",
      "states_included": "AK, CA, HI, ID, MT, NV, OR, UT, WA, WY",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    },
    {
      "region": "International",
      "states_included": "",
      "number_reporting_jobs": "__",
      "low_salary": "__",
      "average_salary": "__",
      "high_salary": "__"
    }
  ],

  "specialty_rankings": [
    { "specialty": "Accounting", "rank": "__", "is_tie": "__" },
    { "specialty": "Business Analytics", "rank": "__", "is_tie": "__" },
    { "specialty": "Entrepreneurship", "rank": "__", "is_tie": "__" },
    { "specialty": "Executive MBA", "rank": "__", "is_tie": "__" },
    { "specialty": "Finance", "rank": "__", "is_tie": "__" },
    { "specialty": "Information Systems", "rank": "__", "is_tie": "__" },
    { "specialty": "International", "rank": "__", "is_tie": "__" },
    { "specialty": "Management", "rank": "__", "is_tie": "__" },
    { "specialty": "Marketing", "rank": "__", "is_tie": "__" },
    { "specialty": "Nonprofit Management", "rank": "__", "is_tie": "__" },
    { "specialty": "Production / Operations", "rank": "__", "is_tie": "__" },
    { "specialty": "Project Management", "rank": "__", "is_tie": "__" },
    { "specialty": "Real Estate", "rank": "__", "is_tie": "__" },
    { "specialty": "Supply Chain / Logistics", "rank": "__", "is_tie": "__" }
  ],

  "program_offerings": {
    "department_concentrations": "__",
    "departments_with_highest_mba_demand": "__",
    "types_of_mba_programs_offered": "__",
    "joint_programs_available": "__",
    "fulltime_program_requires_international_trip": "__",
    "types_of_specialty_masters_offered": "__"
  },

  "specialty_masters_admissions": {
    "us_application_deadline": "__",
    "acceptance_rate": "__",
    "application_fee": "__",
    "test_optional_admissions": "__",
    "applicants": "__",
    "average_age_of_new_entrants": "__",
    "percent_providing_gpa": "__",
    "average_undergraduate_gpa": "__",
    "gpa_range_10th_90th": "__",
    "percent_providing_gmat": "__",
    "average_gmat_domestic": "__",
    "average_gmat_international": "__",
    "gmat_range_10th_90th": "__",
    "students_with_prior_work_experience": "__",
    "average_work_experience_months": "__",
    "undergraduate_majors": "__",
    "percent_providing_gre": "__",
    "gre_score_range_10th_90th": "__"
  },

  "specialty_masters_students": {
    "enrollment": "__",
    "international_students": "__",
    "gender_distribution": "__",
    "student_body": "__"
  },

  "metadata": {
    "data_year": "__",
    "ranking_edition": "__",
    "source_url": "__",
    "extraction_timestamp": "__"
  }
}
```

---

## Field-to-Page Mapping Guide

This table helps the model locate each JSON field on the page when labels differ from key names.

### School Info
| JSON Key | Page Label |
|---|---|
| `us_news_rank` | "#X in Best Business Schools" |
| `us_news_rank_out_of` | "ranked No. X out of Y in Best Business Schools" |
| `us_news_overall_score` | "Overall Score" |
| `school_type` | "School Type" under At-a-Glance |
| `total_enrollment_all_programs` | "Enrollment (ALL Programs)" under At-a-Glance |
| `graduate_enrollment` | "Graduate Enrollment" under Student Population sidebar |
| `total_enrollment` | "Total Enrollment" under Student Population |
| `full_time_degree_seeking_percent` | "Full-Time Degree-Seeking Students" (convert % to decimal) |
| `programs_offered` | "Programs Offered:" under At-a-Glance |

### Tuition & Fees
| JSON Key | Page Label |
|---|---|
| `full_time_tuition_per_year_in_state` | "full-time: $X per year (in-state)" in overview or Expenses table |
| `full_time_tuition_per_year_out_of_state` | "full-time: $X per year (out-of-state)" |
| `required_fees_full_time` | "Required fees (full-time)" in Expenses table |
| `tuition_and_fees_combined_in_state_out_of_state` | "Tuition & Fees (In-State/Out-of-State)" in Cost sidebar |
| `food_housing_books_misc_full_time_mba` | "Food & Housing, Books, and Misc" or "Food and housing, books, and miscellaneous expenses (full-time MBA program)" |
| `executive_mba_total_program_cost_in_state` | "executive: $X total program (in-state)" |

### Student Indebtedness (look under "Student Indebtedness (20XX Graduates)")
| JSON Key | Page Label |
|---|---|
| `average_indebtedness_full_time_mba` | "Average indebtedness (full-time MBA program)" |
| `percentage_with_debt_full_time_mba` | "Percentage with debt (full-time MBA program)" |

### Financial Aid (look under "Financial Aid Availability")
| JSON Key | Page Label |
|---|---|
| `college_funded_aid_available` | "College-funded aid (fellowships, assistantships, grants, or scholarships) available" |
| `fellowships` | "Fellowships" |
| `teaching_assistantships` | "Teaching assistantships" |
| `research_assistantships` | "Research assistantships" |
| `international_students_eligible_for_college_funded_aid` | "International students eligible for college-funded aid" |

### GMAT Data
| JSON Key | Page Label |
|---|---|
| `percent_new_entrants_providing_gmat_new` | "Percent of new entrants providing GMAT scores" |
| `percent_new_entrants_providing_gmat_old` | "Percent of new entrants providing (old) GMAT scores" |
| `average_old_gmat_exam_score` | "Average Old GMAT Exam score" |

### Ranking Scores (Two-Year Averages section)
| JSON Key | Page Label |
|---|---|
| `median_gmat_score_fulltime_new` | "Median GMAT Score of full-time students" |
| `median_gmat_score_fulltime_old` | "Median GMAT Score of full-time students (old exam)" |
| `salaries_by_profession_indicator_rank` | "Salaries by Profession Indicator Rank" |

### Student Body (Full-time MBA)
| JSON Key | Page Label |
|---|---|
| `international_students_percent` | "International students" under Student Body (Full-time MBA Program) |
| `female_percent` / `male_percent` / `other_gender_percent` | Under "Gender distribution" |
| `race_ethnicity.*` | Percentages listed under "Student body (Full-time)" breakdown |

### Career & Salary
| JSON Key | Page Label |
|---|---|
| `full_time_graduates` | "Full-time graduates" under Class of 20XX |
| `full_time_graduates_seeking_employment` | "Full-time graduates known to be seeking employment" |
| `employed_at_graduation_percent` | "Full-time graduates employed at graduation (single year)" |
| `employed_3_months_after_graduation_percent` | "Full-time graduates employed three months after graduation (single year)" |

### Salary Sections
| JSON Section | Page Section |
|---|---|
| `base_salary_overall` | "Base Salary: Overall" |
| `base_salary_us_citizens` | "Base Salary: U.S. Citizens" |
| `base_salary_foreign_nationals` | "Base Salary: Foreign Nationals" |
| `signing_bonus_overall` | "Signing Bonus: Overall" |
| `signing_bonus_us_citizens` | "Signing Bonus: U.S. Citizens" |
| `signing_bonus_foreign_nationals` | "Signing Bonus: Foreign Nationals" |
| `base_salary_by_occupation` | "Base Salary by Occupation" (expanded) |
| `base_salary_by_industry` | "Base Salary by Industry" |
| `base_salary_by_geographic_region` | "Base Salary by Geographic Region" |

### Countries Most Represented
| JSON Key | Page Label |
|---|---|
| `student_body_all_programs.countries_most_represented` | Under "Countries most represented by international students" — extract each country and its percentage |

---

## Usage Instructions

**Input**: Provide the full raw text or HTML content of a US News MBA school profile page with ALL sections expanded.

**How to invoke**: Prepend the page content to this prompt:

```
<page_content>
[PASTE FULL PAGE TEXT OR HTML HERE — ENSURE ALL SECTIONS ARE EXPANDED]
</page_content>

[THIS PROMPT]
```

**Output**: The model returns a single JSON object with all fields populated, or `"NA"` where data is absent.

---

## Example Output (Wharton)

Below is the complete expected output for the Wharton page. Your output for any school must follow this exact structure.

```json
{
  "school_info": {
    "school_name": "University of Pennsylvania",
    "business_school_name": "Wharton",
    "us_news_rank": 1,
    "us_news_rank_out_of": 133,
    "us_news_overall_score": 100,
    "city": "Philadelphia",
    "state": "PA",
    "zip_code": "19104",
    "school_type": "Private",
    "total_enrollment_all_programs": 2304,
    "graduate_enrollment": 1740,
    "total_enrollment": 2304,
    "full_time_degree_seeking_percent": 0.75,
    "programs_offered": "Full-time MBA, Executive MBA, Specialty Masters"
  },

  "tuition_and_fees": {
    "full_time_tuition_per_year_in_state": 84830,
    "full_time_tuition_per_year_out_of_state": 84830,
    "required_fees_full_time": 4670,
    "required_fees_specialty_masters": "NA",
    "tuition_and_fees_combined_in_state_out_of_state": 89500,
    "food_housing_books_misc_full_time_mba": 38216,
    "books_misc_expenses_specialty_masters": "NA",
    "executive_mba_total_program_cost_in_state": 230100,
    "executive_mba_total_program_cost_out_of_state": 230100
  },

  "financial_aid": {
    "financial_aid_available": "Yes",
    "financial_aid_director": "Maxine Adekoya",
    "financial_aid_phone": "(215) 898-8728",
    "college_funded_aid_available": "Yes",
    "fellowships": "NA",
    "teaching_assistantships": "NA",
    "research_assistantships": "NA",
    "international_students_eligible_for_college_funded_aid": "Yes"
  },

  "student_indebtedness_graduates": {
    "average_indebtedness_full_time_mba": "NA",
    "percentage_with_debt_full_time_mba": "NA",
    "average_indebtedness_specialty_masters": "NA",
    "percentage_with_debt_specialty_masters": "NA"
  },

  "application_info": {
    "application_fee": 275,
    "test_optional_admissions": "No",
    "us_application_deadline": "Sep. 04",
    "application_deadlines_fulltime_us": "9/4/24, 1/3/25 and 4/2/25",
    "application_deadlines_fulltime_international": "9/4/24, 1/3/25 and 4/2/25",
    "admissions_process_description": "The Admissions process will include most/all of the following elements: application, essays, transcripts, letters of recommendation, GMAT/GRE, TOEFL, and resume. The interview is a team-based discussion with five to six other applicants which allows interaction with fellow applicants through discourse involving real-world business scenarios. There is also opportunity for an individual exchange.",
    "director_of_admissions": "Blair Mannix",
    "fulltime_mba_phone": "(215) 898-6183",
    "fulltime_mba_email": "mba-admiss@wharton.upenn.edu"
  },

  "admissions_and_enrollment": {
    "total_applicants": 7500,
    "total_accepted_fulltime": "NA",
    "total_enrolled_fulltime": "NA",
    "acceptance_rate": 0.205,
    "average_age_of_new_entrants": 28,
    "students_with_prior_work_experience_count": 858,
    "average_work_experience_months": 60
  },

  "gpa_data": {
    "percent_new_entrants_providing_gpa": 1.0,
    "average_undergraduate_gpa": 3.7,
    "undergraduate_gpa_range_10th_90th": "NA"
  },

  "gmat_data": {
    "percent_new_entrants_providing_gmat_new": 0.0,
    "percent_new_entrants_providing_gmat_old": 0.64,
    "average_gmat_score_domestic": "NA",
    "average_gmat_score_international": "NA",
    "gmat_range_10th_90th": "NA",
    "average_old_gmat_exam_score": 732
  },

  "gre_data": {
    "gre_accepted_for_admissions": "Yes",
    "gre_accepted_as_alternative_to_gmat": "Yes",
    "percent_new_entrants_providing_gre": 0.38,
    "gre_score_range_10th_90th": "NA"
  },

  "toefl_ielts_data": {
    "toefl_required_for_international_students": "No",
    "minimum_toefl_score_required": "NA",
    "mean_toefl_entering_students": "NA",
    "median_toefl_entering_students": "NA",
    "minimum_ielts_score_required": "NA"
  },

  "undergraduate_majors": {
    "business_and_commerce": 0.32,
    "humanities": 0.30,
    "engineering": 0.17,
    "science": 0.12,
    "economics": 0.06,
    "computer_science": 0.03,
    "law": 0.0,
    "social_science": 0.0,
    "other": 0.0
  },

  "ranking_scores_two_year_averages": {
    "overall_score": 100,
    "fulltime_employed_at_graduation_two_yr_avg": 0.778,
    "fulltime_employed_3_months_after_two_yr_avg": 0.904,
    "avg_starting_salary_and_bonus_two_yr_avg": 200724,
    "salaries_by_profession_indicator_rank": 3,
    "median_gmat_score_fulltime_new": "NA",
    "median_gmat_score_fulltime_old": 740,
    "median_undergraduate_gpa": 3.7,
    "acceptance_rate": 0.205,
    "peer_assessment_score_out_of_5": 4.7,
    "recruiter_assessment_score_out_of_5": 4.6
  },

  "student_body_all_programs": {
    "total_enrollment": 2304,
    "countries_most_represented": [
      { "country": "India", "percent": 0.10 },
      { "country": "China", "percent": 0.05 },
      { "country": "Canada", "percent": 0.02 },
      { "country": "United Kingdom", "percent": 0.02 },
      { "country": "South Korea", "percent": 0.01 }
    ]
  },

  "student_body_fulltime_mba": {
    "enrollment": 1740,
    "international_students_percent": 0.303,
    "female_percent": 0.485,
    "male_percent": 0.512,
    "other_gender_percent": 0.008,
    "race_ethnicity": {
      "international": 0.303,
      "white": 0.299,
      "asian": 0.203,
      "black": 0.077,
      "hispanic": 0.072,
      "two_or_more_races": 0.026,
      "unknown": 0.018,
      "american_indian": 0.002,
      "pacific_islander": 0.0
    }
  },

  "career_and_salary_single_year": {
    "full_time_graduates": 915,
    "full_time_graduates_seeking_employment": 634,
    "employed_at_graduation_percent": 0.746,
    "employed_3_months_after_graduation_percent": 0.882
  },

  "base_salary_overall": {
    "total_reporting_base_salary": 455,
    "low_base_salary": 57000,
    "average_base_salary": 173273,
    "high_base_salary": 300000
  },

  "base_salary_us_citizens": {
    "low_base_salary": 81000,
    "average_base_salary": 173957,
    "high_base_salary": 300000
  },

  "base_salary_foreign_nationals": {
    "low_base_salary": 57000,
    "average_base_salary": 171685,
    "high_base_salary": 273000
  },

  "signing_bonus_overall": {
    "total_reporting_signing_bonus": 306,
    "low_signing_bonus": 4000,
    "average_signing_bonus": 39856,
    "high_signing_bonus": 350000
  },

  "signing_bonus_us_citizens": {
    "low_signing_bonus": 4000,
    "average_signing_bonus": 40162,
    "high_signing_bonus": 350000
  },

  "signing_bonus_foreign_nationals": {
    "low_signing_bonus": 5000,
    "average_signing_bonus": 39197,
    "high_signing_bonus": 170000
  },

  "base_salary_by_occupation": [
    {
      "occupation": "Marketing / Sales",
      "number_reporting_jobs": 39,
      "low_salary": 85000,
      "average_salary": 154785,
      "high_salary": 225000
    },
    {
      "occupation": "Operations / Production",
      "number_reporting_jobs": 13,
      "low_salary": 100000,
      "average_salary": 160417,
      "high_salary": 300000
    },
    {
      "occupation": "General Management",
      "number_reporting_jobs": 61,
      "low_salary": 57000,
      "average_salary": 156956,
      "high_salary": 273000
    },
    {
      "occupation": "Finance / Accounting",
      "number_reporting_jobs": 158,
      "low_salary": 100000,
      "average_salary": 178193,
      "high_salary": 263000
    },
    {
      "occupation": "Management Information Systems (MIS)",
      "number_reporting_jobs": 1,
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    },
    {
      "occupation": "Consulting",
      "number_reporting_jobs": 165,
      "low_salary": 94803,
      "average_salary": 178217,
      "high_salary": 229687
    },
    {
      "occupation": "Human Resources",
      "number_reporting_jobs": 1,
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    },
    {
      "occupation": "Other",
      "number_reporting_jobs": 17,
      "low_salary": 115000,
      "average_salary": 188088,
      "high_salary": 275000
    }
  ],

  "base_salary_by_industry": [
    {
      "industry": "Consulting",
      "number_reporting_jobs": 131,
      "low_salary": 94803,
      "average_salary": 183408,
      "high_salary": 229687
    },
    {
      "industry": "Consumer Products",
      "number_reporting_jobs": 6,
      "low_salary": 120000,
      "average_salary": 165333,
      "high_salary": 300000
    },
    {
      "industry": "Financial Services",
      "number_reporting_jobs": 161,
      "low_salary": 90000,
      "average_salary": 176798,
      "high_salary": 263000
    },
    {
      "industry": "Government",
      "number_reporting_jobs": "NA",
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    },
    {
      "industry": "Health Care",
      "number_reporting_jobs": 25,
      "low_salary": 81000,
      "average_salary": 163465,
      "high_salary": 275000
    },
    {
      "industry": "Hospitality",
      "number_reporting_jobs": 1,
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    },
    {
      "industry": "Manufacturing",
      "number_reporting_jobs": 8,
      "low_salary": 130000,
      "average_salary": 163086,
      "high_salary": 185000
    },
    {
      "industry": "Media / Entertainment",
      "number_reporting_jobs": 15,
      "low_salary": 115000,
      "average_salary": 151600,
      "high_salary": 210000
    },
    {
      "industry": "Non-profit",
      "number_reporting_jobs": 9,
      "low_salary": 95000,
      "average_salary": 139333,
      "high_salary": 250000
    },
    {
      "industry": "Energy",
      "number_reporting_jobs": 9,
      "low_salary": 85600,
      "average_salary": 153956,
      "high_salary": 185000
    },
    {
      "industry": "Real Estate",
      "number_reporting_jobs": 9,
      "low_salary": 115000,
      "average_salary": 155833,
      "high_salary": 200000
    },
    {
      "industry": "Retail",
      "number_reporting_jobs": 9,
      "low_salary": 116000,
      "average_salary": 148333,
      "high_salary": 190000
    },
    {
      "industry": "Technology",
      "number_reporting_jobs": 64,
      "low_salary": 57000,
      "average_salary": 162324,
      "high_salary": 273000
    },
    {
      "industry": "Transportation & Logistics",
      "number_reporting_jobs": "NA",
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    },
    {
      "industry": "Other",
      "number_reporting_jobs": 8,
      "low_salary": 210000,
      "average_salary": 223125,
      "high_salary": 235000
    }
  ],

  "base_salary_by_geographic_region": [
    {
      "region": "Northeast",
      "states_included": "CT, MA, ME, NH, NJ, NY, RI, VT",
      "number_reporting_jobs": 55,
      "low_salary": 100000,
      "average_salary": 172129,
      "high_salary": 275000
    },
    {
      "region": "Middle Atlantic",
      "states_included": "DC, DE, MD, PA, VA, WV",
      "number_reporting_jobs": 16,
      "low_salary": 120000,
      "average_salary": 173438,
      "high_salary": 225000
    },
    {
      "region": "South",
      "states_included": "AL, AR, FL, GA, KY, LA, MS, NC, SC, TN",
      "number_reporting_jobs": 214,
      "low_salary": 81000,
      "average_salary": 178842,
      "high_salary": 300000
    },
    {
      "region": "Midwest",
      "states_included": "IA, IL, IN, KS, MI, MN, MO, ND, NE, OH, SD, WI",
      "number_reporting_jobs": 24,
      "low_salary": 100000,
      "average_salary": 165708,
      "high_salary": 193000
    },
    {
      "region": "Southwest",
      "states_included": "AZ, CO, NM, OK, TX",
      "number_reporting_jobs": 24,
      "low_salary": 90000,
      "average_salary": 181958,
      "high_salary": 225000
    },
    {
      "region": "West",
      "states_included": "AK, CA, HI, ID, MT, NV, OR, UT, WA, WY",
      "number_reporting_jobs": 99,
      "low_salary": 95000,
      "average_salary": 171292,
      "high_salary": 273000
    },
    {
      "region": "International",
      "states_included": "",
      "number_reporting_jobs": "NA",
      "low_salary": "NA",
      "average_salary": "NA",
      "high_salary": "NA"
    }
  ],

  "specialty_rankings": [
    { "specialty": "Accounting", "rank": 2, "is_tie": false },
    { "specialty": "Business Analytics", "rank": 4, "is_tie": false },
    { "specialty": "Entrepreneurship", "rank": 6, "is_tie": false },
    { "specialty": "Executive MBA", "rank": 1, "is_tie": false },
    { "specialty": "Finance", "rank": 1, "is_tie": false },
    { "specialty": "Information Systems", "rank": 16, "is_tie": true },
    { "specialty": "International", "rank": 3, "is_tie": false },
    { "specialty": "Management", "rank": 3, "is_tie": false },
    { "specialty": "Marketing", "rank": 2, "is_tie": false },
    { "specialty": "Nonprofit Management", "rank": "NA", "is_tie": false },
    { "specialty": "Production / Operations", "rank": 7, "is_tie": false },
    { "specialty": "Project Management", "rank": "NA", "is_tie": false },
    { "specialty": "Real Estate", "rank": 1, "is_tie": false },
    { "specialty": "Supply Chain / Logistics", "rank": 17, "is_tie": true }
  ],

  "program_offerings": {
    "department_concentrations": "accounting, business analytics, e-commerce, economics, entrepreneurship, ethics, finance, general management, health care administration, human resources management, insurance, international business, leadership, marketing, production/operations management, organizational behavior, public policy, real estate, sports business, supply chain management/logistics, quantitative analysis/statistics and operations research, tax, technology, other",
    "departments_with_highest_mba_demand": "Entrepreneurship, finance, health care administration, other",
    "types_of_mba_programs_offered": "Full-time traditional two year, traditional executive MBA",
    "joint_programs_available": "Architecture, arts, computer science/information systems, education, engineering, healthcare (medicine), healthcare (management), international studies, law, social work, MBA/DMD, MBA/VMD, MBA/MES, MBA/MLA, MBA/MCP, MBA/MSN, MBA/MSED",
    "fulltime_program_requires_international_trip": "No",
    "types_of_specialty_masters_offered": "NA"
  },

  "specialty_masters_admissions": {
    "us_application_deadline": "NA",
    "acceptance_rate": "NA",
    "application_fee": 275,
    "test_optional_admissions": "No",
    "applicants": "NA",
    "average_age_of_new_entrants": "NA",
    "percent_providing_gpa": "NA",
    "average_undergraduate_gpa": "NA",
    "gpa_range_10th_90th": "NA",
    "percent_providing_gmat": "NA",
    "average_gmat_domestic": "NA",
    "average_gmat_international": "NA",
    "gmat_range_10th_90th": "NA",
    "students_with_prior_work_experience": "NA",
    "average_work_experience_months": "NA",
    "undergraduate_majors": "NA",
    "percent_providing_gre": "NA",
    "gre_score_range_10th_90th": "NA"
  },

  "specialty_masters_students": {
    "enrollment": "NA",
    "international_students": "NA",
    "gender_distribution": "NA",
    "student_body": "NA"
  },

  "metadata": {
    "data_year": "2024",
    "ranking_edition": "2025",
    "source_url": "https://premium.usnews.com/best-graduate-schools/top-business-schools/university-of-pennsylvania-01194",
    "extraction_timestamp": "2026-03-08T00:00:00Z"
  }
}
```

---

## Additional Notes

- **Expand all sections** before copying page content. The page has collapsible sections ("SEE MORE COST DATA", "SEE MORE SALARY DATA", "SEE MORE STUDENT DATA", "SEE MORE SPECIALTY DATA") that must all be expanded to capture the full data.
- The page distinguishes between the **new GMAT exam** and the **old GMAT exam** — extract both separately.
- The bar chart under "Applicants / Accepted (full-time) / Enrolled (full-time)" may only show scale markers (7500, 5625, etc.) without exact values for Accepted and Enrolled. If exact counts are not readable as text, set to `"NA"`.
- For `base_salary_by_occupation` and `base_salary_by_industry`: when only 1 person reported a job in a category, the page typically shows no salary data — set low/average/high to `"NA"`.
- For `undergraduate_majors`, the page may note "Not Specified is not included in this breakdown due to an enrollment of 0%". Only extract the listed categories.
- For `specialty_rankings`, if a specialty is not listed on the page, set rank to `"NA"` and `is_tie` to `false`.
- `data_year` comes from the footer note: "Business School details based on XXXX data."
- `ranking_edition` is the year from the rankings header (e.g., "2025 Rankings").
- If additional data points appear that are **not** in this template, append them under a new top-level key `"additional_fields"` as key-value pairs following the same numeric cleaning rules.
