import os
import re
from typing import List, Tuple, Any

def extract(file_path: str) -> List[Tuple[str, str, Any, str, str]]:
    """
    Extracts raw data from free-text recruiter notes.
    """
    results = []
    if not os.path.exists(file_path):
        print(f"Warning: Notes file not found at {file_path}")
        return results

    source_name = "recruiter_notes"
    method = "regex_notes"
    record_id = f"notes_{os.path.basename(file_path)}"

    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            text = f.read()
            
        # 1. Emails
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_pattern, text)
        if emails:
            emails = list(dict.fromkeys([e.strip() for e in emails]))
            results.append((record_id, "emails", emails, source_name, method))

        # 2. Candidate Name
        # Look for "Candidate <Name>" or "Candidate: <Name>"
        name_match = re.search(r'Candidate\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
        if name_match:
            results.append((record_id, "full_name", name_match.group(1).strip(), source_name, method))

        # 3. Years of experience
        # e.g., "6.5 years of experience" or "5 years"
        exp_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:years?)(?:\s+of\s+experience)?\b', text, re.IGNORECASE)
        if exp_match:
            try:
                years = float(exp_match.group(1))
                results.append((record_id, "years_experience", years, source_name, method))
            except ValueError:
                pass

        # 4. Location
        # e.g. "located in Mumbai"
        loc_match = re.search(r'\blocated\s+in\s+([A-Z][a-zA-Z\s]+?)(?:\.|\n|$)', text)
        if loc_match:
            results.append((record_id, "location", loc_match.group(1).strip(), source_name, method))

    except Exception as e:
        print(f"Error reading notes {file_path}: {e}")
        return []

    return results
