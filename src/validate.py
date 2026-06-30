import jsonschema
from typing import Dict, Any, List, Optional

def get_json_type(field_type: str, nullable: bool = False) -> Any:
    base_type = "string"
    if field_type == "string":
        base_type = "string"
    elif field_type == "number":
        base_type = "number"
    elif field_type == "integer":
        base_type = "integer"
    elif field_type == "boolean":
        base_type = "boolean"
    elif field_type == "array":
        base_type = "array"
    
    if nullable:
        return [base_type, "null"]
    return base_type

def build_schema_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically builds a JSON schema based on the fields specified in the config.
    Supports dotted path structures.
    """
    properties: Dict[str, Any] = {}
    required_fields: List[str] = []

    for field in config.get("fields", []):
        path = field.get("path")
        req = field.get("required", False)
        nullable = (field.get("on_missing") == "null") and not req
        f_type = get_json_type(field.get("type", "string"), nullable=nullable)

        if not path:
            continue

        parts = path.split('.')
        curr_prop = properties
        
        # Build nested object structures in schema properties
        for part in parts[:-1]:
            if part not in curr_prop:
                curr_prop[part] = {
                    "type": "object",
                    "properties": {}
                }
            elif curr_prop[part].get("type") != "object":
                # Overwrite type if it was previously set as scalar
                curr_prop[part] = {
                    "type": "object",
                    "properties": {}
                }
            curr_prop = curr_prop[part]["properties"]

        curr_prop[parts[-1]] = {"type": f_type}
        
        if req:
            # Handle top-level required properties
            if len(parts) == 1:
                required_fields.append(parts[0])

    if config.get("include_confidence", True):
        properties["overall_confidence"] = {"type": "number"}
    if config.get("include_provenance", True):
        properties["provenance"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "source": {"type": "string"},
                    "method": {"type": "string"},
                    "value": {"type": ["string", "null"]}
                },
                "required": ["field", "source", "method"]
            }
        }

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required_fields,
        "additionalProperties": True # allow other helper keys if any
    }
    return schema

def get_default_schema() -> Dict[str, Any]:
    """
    Returns default schema corresponding to the CanonicalProfile dump.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string"},
            "full_name": {"type": ["string", "null"]},
            "emails": {"type": "array", "items": {"type": "string"}},
            "phones": {"type": "array", "items": {"type": "string"}},
            "location": {"type": ["string", "null"]},
            "links": {"type": "array", "items": {"type": "string"}},
            "headline": {"type": ["string", "null"]},
            "years_experience": {"type": ["number", "null"]},
            "skills": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "confidence": {"type": "number"},
                        "sources": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["name", "confidence"]
                }
            },
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "title": {"type": ["string", "null"]},
                        "start_date": {"type": ["string", "null"]},
                        "end_date": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["company"]
                }
            },
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution": {"type": "string"},
                        "degree": {"type": ["string", "null"]},
                        "field_of_study": {"type": ["string", "null"]},
                        "start_date": {"type": ["string", "null"]},
                        "end_date": {"type": ["string", "null"]}
                    },
                    "required": ["institution"]
                }
            },
            "provenance": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "source": {"type": "string"},
                        "method": {"type": "string"},
                        "value": {"type": ["string", "null"]}
                    },
                    "required": ["field", "source", "method"]
                }
            },
            "overall_confidence": {"type": "number"}
        },
        "required": ["candidate_id"]
    }

def validate_profile(profile_dict: Dict[str, Any], config: Optional[Dict[str, Any]]) -> List[str]:
    """
    Validates a projected profile dict against the schema.
    Returns list of validation error messages.
    """
    if config and "fields" in config:
        schema = build_schema_from_config(config)
    else:
        schema = get_default_schema()

    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for error in validator.iter_errors(profile_dict):
        errors.append(f"Field path '{'.'.join(str(p) for p in error.path)}': {error.message}")
        
    return errors
