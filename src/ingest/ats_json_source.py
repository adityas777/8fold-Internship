import json
import os
from typing import List, Tuple, Any, Dict

def extract(file_path: str) -> List[Tuple[str, str, Any, str, str]]:
    """
    Extracts raw data from an ATS JSON source.
    Returns list of tuples: (record_id, field_path, raw_value, source_name, method)
    """
    results = []
    if not os.path.exists(file_path):
        print(f"Warning: ATS JSON file not found at {file_path}")
        return results

    source_name = "ats_json"
    method = "json_parser"

    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Standardize single candidate vs list of candidates
        if isinstance(data, dict):
            candidates = [data]
        elif isinstance(isinstance(data, list), list):
            candidates = data
        else:
            candidates = [data]

        for idx, cand in enumerate(candidates):
            record_id = f"ats_cand_{idx}"
            
            # 1. Full name
            first = cand.get("first_name", "").strip()
            last = cand.get("last_name", "").strip()
            name = cand.get("name", "").strip()
            if not name and (first or last):
                name = f"{first} {last}".strip()
            if name:
                results.append((record_id, "full_name", name, source_name, method))

            # 2. Emails (might be list or single)
            email_field = cand.get("email") or cand.get("emails")
            if email_field:
                results.append((record_id, "emails", email_field, source_name, method))

            # 3. Phones
            phone_field = cand.get("phone") or cand.get("phones") or cand.get("telephone")
            if phone_field:
                results.append((record_id, "phones", phone_field, source_name, method))

            # 4. Location
            loc = cand.get("location") or cand.get("city") or cand.get("address")
            if isinstance(loc, dict):
                loc_str = ", ".join([v for v in loc.values() if isinstance(v, str)])
            else:
                loc_str = str(loc) if loc else ""
            if loc_str:
                results.append((record_id, "location", loc_str.strip(), source_name, method))

            # 5. Headline
            headline = cand.get("headline") or cand.get("title") or cand.get("summary")
            if headline:
                results.append((record_id, "headline", headline.strip(), source_name, method))

            # 6. Years experience
            years = cand.get("years_experience") or cand.get("experience_years")
            if years is not None:
                results.append((record_id, "years_experience", years, source_name, method))

            # 7. Skills (list of strings or string)
            skills = cand.get("skills")
            if skills:
                results.append((record_id, "skills", skills, source_name, method))

            # 8. Experience
            exp = cand.get("experience") or cand.get("work_history") or cand.get("jobs")
            if isinstance(exp, list):
                results.append((record_id, "experience", exp, source_name, method))

            # 9. Education
            edu = cand.get("education") or cand.get("education_history") or cand.get("schools")
            if isinstance(edu, list):
                results.append((record_id, "education", edu, source_name, method))

            # 10. Links
            links = cand.get("links") or cand.get("urls") or cand.get("websites")
            if links:
                results.append((record_id, "links", links, source_name, method))

    except Exception as e:
        print(f"Error reading ATS JSON {file_path}: {e}")
        return []

    return results
