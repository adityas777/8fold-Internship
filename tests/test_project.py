import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import CanonicalProfile, SkillEntry, ProvenanceEntry
from src.project import project_profile
from src.validate import validate_profile, build_schema_from_config

def test_project_profile_default():
    profile = CanonicalProfile(
        candidate_id="cand_1",
        full_name="Jane Doe",
        emails=["jane@example.com"],
        overall_confidence=0.85
    )
    # Default projection (no config) maps everything
    res = project_profile(profile, None)
    assert res["candidate_id"] == "cand_1"
    assert res["full_name"] == "Jane Doe"
    assert res["emails"] == ["jane@example.com"]
    assert res["overall_confidence"] == 0.85

def test_project_profile_custom_config():
    profile = CanonicalProfile(
        candidate_id="cand_1",
        full_name="Jane Doe",
        emails=["jane@example.com"],
        location="Mumbai, India",
        overall_confidence=0.85,
        provenance=[ProvenanceEntry(field="full_name", source="resume", method="regex_heuristics")]
    )
    
    # Custom configuration
    config = {
        "fields": [
            { "path": "id", "from": "candidate_id", "type": "string", "required": True },
            { "path": "name", "from": "full_name", "type": "string", "required": True },
            { "path": "contact.email", "from": "emails", "type": "array", "required": False, "on_missing": "omit" },
            { "path": "work_location", "from": "location", "type": "string", "required": False, "on_missing": "null" },
            { "path": "missing_field", "from": "headline", "type": "string", "required": False, "on_missing": "omit" }
        ],
        "include_confidence": True,
        "include_provenance": False
    }
    
    res = project_profile(profile, config)
    
    assert res["id"] == "cand_1"
    assert res["name"] == "Jane Doe"
    assert res["contact"]["email"] == ["jane@example.com"]
    assert res["work_location"] == "Mumbai, India"
    assert "missing_field" not in res
    assert res["overall_confidence"] == 0.85
    assert "provenance" not in res

def test_validation():
    # Schema validation test
    config = {
        "fields": [
            { "path": "id", "from": "candidate_id", "type": "string", "required": True },
            { "path": "name", "from": "full_name", "type": "string", "required": True }
        ],
        "include_confidence": True,
        "include_provenance": False
    }
    
    # Valid output
    valid_data = {
        "id": "cand_1",
        "name": "Jane Doe",
        "overall_confidence": 0.90
    }
    errors = validate_profile(valid_data, config)
    assert len(errors) == 0
    
    # Invalid output (missing required 'name' field)
    invalid_data = {
        "id": "cand_1",
        "overall_confidence": 0.90
    }
    errors = validate_profile(invalid_data, config)
    assert len(errors) == 1
    assert "name" in errors[0]
