import os
import logging
from typing import List, Dict, Any, Optional

from src.ingest import csv_source, ats_json_source, github_source, resume_source, notes_source
from src.merge import merge
from src.project import project_profile
from src.validate import validate_profile

logger = logging.getLogger("eightfold_pipeline")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def detect_and_extract(source: str) -> List[tuple]:
    """
    Detects the source type based on extension, shape, or URL pattern,
    and runs the appropriate ingester to return raw tuples.
    """
    source_lower = source.strip().lower()
    
    # 1. GitHub API Source
    if "github.com" in source_lower or (not os.path.exists(source) and len(source.split()) == 1 and not source.endswith(('.csv', '.json', '.pdf', '.docx', '.txt'))):
        logger.info(f"Detected GitHub source for: {source}")
        return github_source.extract(source)

    # 2. File Sources
    if not os.path.exists(source):
        logger.warning(f"Source file/URL not found: {source}")
        return []

    ext = os.path.splitext(source_lower)[1]
    
    if ext == ".csv":
        logger.info(f"Detected CSV source: {source}")
        return csv_source.extract(source)
    elif ext == ".json":
        logger.info(f"Detected ATS JSON source: {source}")
        return ats_json_source.extract(source)
    elif ext in [".pdf", ".docx", ".doc"]:
        logger.info(f"Detected Resume source: {source}")
        return resume_source.extract(source)
    elif ext == ".txt":
        # Check if it looks like recruiter notes
        if "notes" in source_lower:
            logger.info(f"Detected Recruiter Notes source: {source}")
            return notes_source.extract(source)
        else:
            logger.info(f"Defaulting to Recruiter Notes parser for text file: {source}")
            return notes_source.extract(source)
            
    logger.warning(f"Unknown source type for: {source}. Skipping.")
    return []

def run_pipeline(sources: List[str], config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Orchestrates the entire profile pipeline.
    Runs: detect -> extract -> normalize -> merge -> confidence -> project -> validate
    """
    raw_tuples = []
    
    # Ingest and Extract
    for s in sources:
        try:
            extracted = detect_and_extract(s)
            raw_tuples.extend(extracted)
        except Exception as e:
            logger.error(f"Skipping bad source {s}: {e}")

    if not raw_tuples:
        logger.warning("No raw candidate data extracted from any sources.")
        return []

    # Entity Resolution & Merging (Normalization is run inside merge.py per-field)
    logger.info("Merging profiles and resolving entities...")
    canonical_profiles = merge(raw_tuples)
    logger.info(f"Merged raw data into {len(canonical_profiles)} canonical candidate profiles.")

    # Projection & Schema Validation
    projected_outputs = []
    for profile in canonical_profiles:
        try:
            # Project using config
            projected = project_profile(profile, config)
            
            # Validate output dict
            validation_errors = validate_profile(projected, config)
            if validation_errors:
                logger.warning(f"Validation errors for candidate {profile.candidate_id}:")
                for err in validation_errors:
                    logger.warning(f"  - {err}")
            
            projected_outputs.append(projected)
        except Exception as e:
            logger.error(f"Failed to project candidate profile {profile.candidate_id}: {e}")

    return projected_outputs
