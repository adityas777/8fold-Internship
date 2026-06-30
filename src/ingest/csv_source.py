import csv
import os
from typing import List, Tuple, Any

def extract(file_path: str) -> List[Tuple[str, str, Any, str, str]]:
    """
    Extracts raw data from a Recruiter CSV export.
    Returns list of tuples: (record_id, field_path, raw_value, source_name, method)
    """
    results = []
    if not os.path.exists(file_path):
        print(f"Warning: CSV file not found at {file_path}")
        return results

    source_name = "recruiter_csv"
    method = "csv_reader"

    try:
        with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            # Map headers (case-insensitive, strip whitespace)
            header_map = {}
            for h in reader.fieldnames or []:
                clean_h = h.strip().lower()
                header_map[clean_h] = h

            # Map known header categories to canonical fields
            field_mappings = {
                "full_name": ["name", "full_name", "candidate_name", "candidate name"],
                "emails": ["email", "email_address", "email address", "emails"],
                "phones": ["phone", "phone_number", "phone number", "phones"],
                "location": ["location", "city", "address", "current_location"],
                "years_experience": ["years_experience", "experience_years", "exp", "experience"],
                "headline": ["title", "job_title", "headline", "current_company"]
            }

            for idx, row in enumerate(reader):
                record_id = f"csv_row_{idx}"
                
                # We also want to capture current company and title if available
                company = ""
                title = ""

                # Extract individual mapped fields
                for canonical_field, aliases in field_mappings.items():
                    for alias in aliases:
                        if alias in header_map:
                            val = row.get(header_map[alias])
                            if val:
                                val = val.strip()
                                if val:
                                    if canonical_field == "headline" and "title" in alias:
                                        title = val
                                    elif "company" in alias:
                                        company = val
                                    
                                    # CSV splits email/phones if comma-separated, but we keep it raw first
                                    results.append((record_id, canonical_field, val, source_name, method))

                # Handle experience summary if we have company/title
                if company or title:
                    exp_item = {
                        "company": company or "Unknown",
                        "title": title or "Unknown",
                        "start_date": None,
                        "end_date": "Present",
                        "description": "Imported from Recruiter CSV"
                    }
                    results.append((record_id, "experience", [exp_item], source_name, method))

    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return []

    return results
