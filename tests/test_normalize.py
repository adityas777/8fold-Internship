import pytest
import sys
import os

# Adjust path to find src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill

def test_normalize_phone():
    # E.164 conversion
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("9876543210", default_region="IN") == "+919876543210"
    assert normalize_phone("+1 (415) 555-2671") == "+14155552671"
    # Garbage input fallback
    assert normalize_phone("invalid phone") is None
    assert normalize_phone("") is None

def test_normalize_date():
    # Standard YYYY-MM
    assert normalize_date("2022-03") == "2022-03"
    assert normalize_date("2020/01") == "2020-01"
    # Free-text parse
    assert normalize_date("March 2022") == "2022-03"
    assert normalize_date("Jan 2020") == "2020-01"
    # Present mapping
    assert normalize_date("Present") is None
    assert normalize_date("current") is None
    # Invalid date
    assert normalize_date("not a date") is None
    assert normalize_date("") is None

def test_normalize_country():
    # Direct matches
    assert normalize_country("USA") == "US"
    assert normalize_country("United States") == "US"
    assert normalize_country("India") == "IN"
    # Location string parsing
    assert normalize_country("Mumbai, India") == "IN"
    assert normalize_country("Seattle, WA, USA") == "US"
    # Invalid/unmapped country
    assert normalize_country("Wakanda") is None
    assert normalize_country("") is None

def test_normalize_skill():
    # Aliases
    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("react.js") == "React"
    assert normalize_skill("golang") == "Go"
    assert normalize_skill("nodejs") == "Node.js"
    # Fallback to title-case
    assert normalize_skill("django") == "Django"
    assert normalize_skill("some-weird-skill") == "Some-Weird-Skill"
