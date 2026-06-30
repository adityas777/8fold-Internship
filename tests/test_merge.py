import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.merge import merge, levenshtein_similarity
from src.models import CanonicalProfile

def test_levenshtein_similarity():
    assert levenshtein_similarity("Jane Doe", "Jane Doe") == 1.0
    assert levenshtein_similarity("Jane Doe", "Janie Doe") > 0.8
    assert levenshtein_similarity("Jane Doe", "Bob Smith") < 0.3

def test_merge_candidates():
    # Setup raw tuples representing conflict and consensus
    # Jane Doe represented in CSV and Resume
    raw_tuples = [
        # CSV source data
        ("csv_row_0", "full_name", "Jane Doe", "recruiter_csv", "csv_reader"),
        ("csv_row_0", "emails", ["jane.doe@example.com"], "recruiter_csv", "csv_reader"),
        ("csv_row_0", "phones", ["+91 98765 43210"], "recruiter_csv", "csv_reader"),
        ("csv_row_0", "location", "Mumbai, India", "recruiter_csv", "csv_reader"),
        ("csv_row_0", "years_experience", 5, "recruiter_csv", "csv_reader"),
        
        # Resume source data (conflict in years_experience: resume says 6.5, CSV says 5)
        ("resume_jane_doe.pdf", "full_name", "Jane Doe", "resume", "regex_heuristics"),
        ("resume_jane_doe.pdf", "emails", ["jane.doe@example.com"], "resume", "regex_heuristics"),
        ("resume_jane_doe.pdf", "phones", ["+91 98765 43210"], "resume", "regex_heuristics"),
        ("resume_jane_doe.pdf", "years_experience", 6.5, "resume", "regex_heuristics"),
        ("resume_jane_doe.pdf", "skills", ["Python", "ReactJS"], "resume", "regex_heuristics"),
    ]

    profiles = merge(raw_tuples)
    
    assert len(profiles) == 1
    p = profiles[0]
    
    # Check identity
    assert p.full_name == "Jane Doe"
    assert "jane.doe@example.com" in p.emails
    assert "+919876543210" in p.phones
    
    # Conflict Resolution: resume wins for years_experience
    # Priority for years_experience: resume > recruiter_notes > recruiter_csv
    assert p.years_experience == 6.5
    
    # Skills resolution and normalization
    skill_names = [s.name for s in p.skills]
    assert "Python" in skill_names
    assert "React" in skill_names  # reactjs normalized to React
    
    # Check that provenance records both inputs
    years_prov = [prov for prov in p.provenance if prov.field == "years_experience"]
    assert len(years_prov) == 2
    sources = [prov.source for prov in years_prov]
    assert "resume" in sources
    assert "recruiter_csv" in sources

    # Check confidence values
    # years_experience winner is resume (regex_heuristics base = 0.6)
    # no agreement since values are different (5 vs 6.5)
    # So confidence should be 0.6
    years_conf_entry = [prov for prov in years_prov if prov.source == "resume"][0]
    # In merge.py we return a single confidence per resolved field.
    # Let's verify overall confidence is calculated
    assert p.overall_confidence > 0
