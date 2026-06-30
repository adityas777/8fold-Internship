import re
from datetime import datetime
from typing import Optional
import phonenumbers
from dateutil import parser as date_parser

# Lookup for country aliases
COUNTRY_MAP = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "india": "IN",
    "ind": "IN",
    "in": "IN",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "germany": "DE",
    "deutschland": "DE",
    "de": "DE",
    "canada": "CA",
    "ca": "CA"
}

# Skill alias map
SKILL_MAP = {
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "GCP",
    "git": "Git",
    "golang": "Go",
    "go": "Go",
    "java": "Java",
    "spring": "Spring",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "rust": "Rust",
    "python": "Python",
    "py": "Python",
    "angular": "Angular",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "node": "Node.js",
    "nodejs": "Node.js"
}

def normalize_phone(raw: str, default_region: str = "IN") -> Optional[str]:
    """
    Standardize raw phone number to E.164 format.
    """
    if not raw:
        return None
    try:
        # Remove common characters that might confuse phonenumbers if not structured
        clean_raw = raw.strip()
        parsed = phonenumbers.parse(clean_raw, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    
    # Try backup cleaner regex for raw digits
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10 and default_region == "IN":
        return f"+91{digits}"
    elif len(digits) == 11 and digits.startswith("1") and default_region == "US":
        return f"+{digits}"
    
    return None

def normalize_date(raw: str) -> Optional[str]:
    """
    Normalizes a date string to YYYY-MM format.
    Returns None if date represents "Present" or is invalid.
    """
    if not raw:
        return None
        
    clean_raw = raw.strip().lower()
    if clean_raw in ["present", "current", "now", "till date"]:
        return None

    # Handle standard YYYY-MM or YYYY-MM-DD pattern directly
    match = re.match(r'^(\d{4})[-/](\d{1,2})', clean_raw)
    if match:
        year, month = match.group(1), match.group(2)
        return f"{year}-{int(month):02d}"

    # Try parsing via dateutil
    try:
        parsed_dt = date_parser.parse(clean_raw, fuzzy=True)
        return parsed_dt.strftime("%Y-%m")
    except Exception:
        pass

    # Regex search for year-month or month-year sequences
    # Look for 4 digits (year)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', clean_raw)
    if year_match:
        year = year_match.group(1)
        # Look for month name or digit
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        for i, m in enumerate(months):
            if m in clean_raw:
                return f"{year}-{(i+1):02d}"
        # If no month name, default to January
        return f"{year}-01"

    return None

def normalize_country(raw: str) -> Optional[str]:
    """
    Normalizes country to ISO-3166 alpha-2.
    """
    if not raw:
        return None
    
    clean_raw = raw.strip().lower()
    
    # Check direct map
    if clean_raw in COUNTRY_MAP:
        return COUNTRY_MAP[clean_raw]
        
    # Attempt to extract country from location string like "Mumbai, India"
    for word in re.split(r'[,.\s]+', clean_raw):
        if word in COUNTRY_MAP:
            return COUNTRY_MAP[word]
            
    return None

def normalize_skill(raw: str) -> str:
    """
    Normalizes skill name using alias map or title-cases as fallback.
    """
    clean_raw = raw.strip().lower()
    if clean_raw in SKILL_MAP:
        return SKILL_MAP[clean_raw]
    return raw.strip().title()
