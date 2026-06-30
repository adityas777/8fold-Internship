import re
from typing import Dict, Any, List, Optional
from src.models import CanonicalProfile

def set_nested_value(d: Dict[str, Any], path: str, value: Any) -> None:
    """
    Sets a value in a nested dictionary using dot notation (e.g. 'contact.email').
    """
    parts = path.split('.')
    current = d
    for part in parts[:-1]:
        # Handle list indices if present (e.g. skills[0])
        # For simplicity, we just use string dict keys
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

def get_nested_value(obj: Any, path: str) -> Any:
    """
    Gets a value from a Pydantic model or dict using dot notation.
    """
    parts = path.split('.')
    current = obj
    for part in parts:
        if current is None:
            return None
        
        # Check if current is a dict or model
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current

def project_profile(profile: CanonicalProfile, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Projects a CanonicalProfile into a dictionary structure based on runtime config.
    """
    # Default Config: Output everything
    if not config or "fields" not in config:
        output = profile.model_dump()
        return output

    output: Dict[str, Any] = {}
    
    # Process mapped fields
    for field_conf in config["fields"]:
        output_path = field_conf.get("path")
        canonical_from = field_conf.get("from")
        field_type = field_conf.get("type", "string")
        required = field_conf.get("required", False)
        on_missing = field_conf.get("on_missing", "null")

        if not output_path or not canonical_from:
            continue

        # Get value from canonical record
        val = get_nested_value(profile, canonical_from)

        # Handle missing values
        if val is None or (isinstance(val, list) and not val):
            if required and on_missing == "error":
                raise ValueError(f"Required field '{output_path}' (from '{canonical_from}') is missing for candidate {profile.candidate_id}.")
            
            if on_missing == "omit":
                continue
            elif on_missing == "error":
                # Default to null mapping but log warning, or raise error
                raise ValueError(f"Required field '{output_path}' is missing.")
            else:  # on_missing == "null" or fallback
                set_nested_value(output, output_path, None)
                continue

        # Perform basic type casting/assertion
        if field_type == "string":
            if isinstance(val, list):
                val = ", ".join(str(x) for x in val)
            else:
                val = str(val)
        elif field_type == "number":
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0.0
        elif field_type == "integer":
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = 0
        elif field_type == "boolean":
            val = bool(val)
        elif field_type == "array":
            # Ensure it is a list of serializable structures
            if not isinstance(val, list):
                val = [val]
            
            # If it's a list of SkillEntry/Experience/Education models, serialize them to dicts
            serialized_list = []
            for item in val:
                if hasattr(item, "model_dump"):
                    serialized_list.append(item.model_dump())
                else:
                    serialized_list.append(item)
            val = serialized_list

        set_nested_value(output, output_path, val)

    # Handle include_confidence
    if config.get("include_confidence", True):
        output["overall_confidence"] = profile.overall_confidence

    # Handle include_provenance
    if config.get("include_provenance", True):
        output["provenance"] = [p.model_dump() for p in profile.provenance]

    return output
