"""
JSON Schema utilities for converting Pydantic models to JSON Schema.
Used in Plan A for structured outputs with OpenAI.
"""

from typing import Type, Dict, Any
from pydantic import BaseModel
import json


def pydantic_to_json_schema(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema format for OpenAI structured outputs.
    
    Args:
        model_class: Pydantic model class
        
    Returns:
        JSON Schema dictionary
    """
    # Use Pydantic's built-in schema generation
    schema = model_class.model_json_schema()
    
    # OpenAI expects a specific format for structured outputs
    # We need to ensure the schema is compatible with OpenAI's requirements
    json_schema = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    
    # Convert Pydantic schema to OpenAI-compatible JSON Schema
    if "properties" in schema:
        for field_name, field_info in schema["properties"].items():
            # Skip internal fields
            if field_name.startswith("_"):
                continue
            
            json_schema["properties"][field_name] = _convert_field_schema(field_info)
            
            # Add to required if field is required
            if field_name in schema.get("required", []):
                json_schema["required"].append(field_name)
    
    return json_schema


def _convert_field_schema(field_info: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Pydantic field schema to JSON Schema format"""
    field_type = field_info.get("type")
    
    if field_type == "string":
        return {"type": "string"}
    
    elif field_type == "integer":
        return {"type": "integer"}
    
    elif field_type == "number":
        return {"type": "number"}
    
    elif field_type == "boolean":
        return {"type": "boolean"}
    
    elif field_type == "array":
        items = field_info.get("items", {})
        if isinstance(items, dict):
            if "type" in items:
                return {
                    "type": "array",
                    "items": {"type": items["type"]}
                }
            elif "$ref" in items:
                # Handle nested models (like founders)
                return {
                    "type": "array",
                    "items": {"type": "object", "properties": {}}
                }
            elif "anyOf" in items:
                # Handle union types
                return {
                    "type": "array",
                    "items": {"type": "string"}  # Default to string for simplicity
                }
        return {"type": "array", "items": {"type": "string"}}
    
    elif field_type == "object":
        properties = field_info.get("properties", {})
        return {
            "type": "object",
            "properties": {k: _convert_field_schema(v) for k, v in properties.items()},
            "additionalProperties": False
        }
    
    elif "anyOf" in field_info:
        # Handle Optional types (Union[Type, None])
        # Extract the non-None type
        any_of = field_info["anyOf"]
        non_null_type = next((t for t in any_of if t.get("type") != "null"), None)
        if non_null_type:
            return _convert_field_schema(non_null_type)
        return {"type": "string"}  # Default fallback
    
    # Default fallback
    return {"type": "string"}


def get_extraction_schema(extract_type: str) -> Dict[str, Any]:
    """
    Get JSON Schema for a specific extraction type.
    
    Args:
        extract_type: Type of extraction (progress, financial, market, company, team)
        
    Returns:
        JSON Schema dictionary
    """
    from app.core.models import (
        ProgressData,
        FinancialData,
        MarketData,
        CompanyData,
        TeamData,
    )
    
    model_map = {
        "progress": ProgressData,
        "financial": FinancialData,
        "market": MarketData,
        "company": CompanyData,
        "team": TeamData,
    }
    
    if extract_type not in model_map:
        raise ValueError(f"Unknown extraction type: {extract_type}")
    
    return pydantic_to_json_schema(model_map[extract_type])

