"""
Data validation and type coercion utility for fixing common extraction issues.
Used in Plans B and D to ensure data types match Pydantic model expectations.
"""

from typing import Any, Dict, List, Optional, Union
import json


class DataValidator:
    """Validates and fixes common data type mismatches in extracted data"""

    @staticmethod
    def validate_and_fix(data: Dict[str, Any], expected_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix data according to expected schema.
        
        Args:
            data: Raw extracted data dictionary
            expected_schema: Schema defining expected types for each field
            
        Returns:
            Fixed data dictionary with correct types
        """
        fixed_data = {}
        
        for field_name, field_type in expected_schema.items():
            if field_name not in data:
                continue
                
            value = data[field_name]
            
            # Skip None/null values
            if value is None:
                fixed_data[field_name] = None
                continue
            
            # Fix based on expected type
            fixed_value = DataValidator._fix_field_value(value, field_type, field_name)
            fixed_data[field_name] = fixed_value
        
        return fixed_data
    
    @staticmethod
    def _fix_field_value(value: Any, expected_type: Any, field_name: str) -> Any:
        """Fix a single field value to match expected type"""
        
        # Handle string fields - convert int/float to string
        if expected_type == str or (isinstance(expected_type, type) and expected_type == str):
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, dict):
                # Flatten dict to string representation
                return json.dumps(value) if value else None
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                # Convert list of dicts to list of strings
                return [json.dumps(item) if item else "" for item in value]
            return str(value) if value is not None else None
        
        # Handle list of strings - flatten dicts to strings
        if expected_type == List[str] or (isinstance(expected_type, type) and issubclass(expected_type, list)):
            if not isinstance(value, list):
                return [str(value)] if value is not None else []
            
            fixed_list = []
            for item in value:
                if isinstance(item, dict):
                    # Convert dict to string representation
                    fixed_list.append(json.dumps(item))
                elif isinstance(item, (int, float)):
                    fixed_list.append(str(item))
                else:
                    fixed_list.append(str(item) if item is not None else "")
            
            return fixed_list
        
        # Handle list of dicts (for founders)
        if expected_type == List[Dict[str, str]]:
            if not isinstance(value, list):
                return []
            
            fixed_list = []
            for item in value:
                if isinstance(item, dict):
                    # Ensure all values in dict are strings
                    fixed_dict = {}
                    for k, v in item.items():
                        fixed_dict[k] = str(v) if v is not None else None
                    fixed_list.append(fixed_dict)
                elif isinstance(item, str):
                    # If it's a string, try to parse as JSON or create simple dict
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            fixed_list.append(parsed)
                        else:
                            fixed_list.append({"name": item})
                    except:
                        fixed_list.append({"name": item})
            
            return fixed_list
        
        # Handle int fields
        if expected_type == int or (isinstance(expected_type, type) and expected_type == int):
            if isinstance(value, str):
                try:
                    return int(float(value))  # Handle "45.0" -> 45
                except:
                    return None
            if isinstance(value, (int, float)):
                return int(value)
            return None
        
        # Handle dict fields
        if expected_type == Dict[str, str] or (isinstance(expected_type, type) and issubclass(expected_type, dict)):
            if isinstance(value, dict):
                # Ensure all values are strings
                return {k: str(v) if v is not None else None for k, v in value.items()}
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return {k: str(v) if v is not None else None for k, v in parsed.items()}
                except:
                    pass
            return None
        
        return value
    
    @staticmethod
    def fix_progress_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in progress extraction data"""
        expected_schema = {
            "arr": str,
            "mrr": str,
            "burn_rate": str,
            "runway_months": int,
            "churn_rate": str,
            "growth_rate_mom": str,
            "growth_rate_yoy": str,
            "customer_count": str,  # Must be string!
            "cac": str,
            "ltv": str,
        }
        return DataValidator.validate_and_fix(data, expected_schema)
    
    @staticmethod
    def fix_team_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in team extraction data"""
        fixed_data = data.copy()
        
        # Fix founders - should be List[Dict[str, str]]
        if "founders" in fixed_data and fixed_data["founders"]:
            if isinstance(fixed_data["founders"], list):
                fixed_founders = []
                for item in fixed_data["founders"]:
                    if isinstance(item, dict):
                        fixed_founders.append({k: str(v) if v is not None else None for k, v in item.items()})
                    elif isinstance(item, str):
                        fixed_founders.append({"name": item})
                fixed_data["founders"] = fixed_founders
        
        # Fix list fields that should be List[str] not List[Dict]
        list_string_fields = ["key_employees", "advisors", "board_members", "past_exits", "relevant_experience"]
        for field in list_string_fields:
            if field in fixed_data and fixed_data[field]:
                if isinstance(fixed_data[field], list):
                    fixed_list = []
                    for item in fixed_data[field]:
                        if isinstance(item, dict):
                            # Convert dict to string representation
                            fixed_list.append(json.dumps(item))
                        elif isinstance(item, (int, float)):
                            fixed_list.append(str(item))
                        else:
                            fixed_list.append(str(item) if item is not None else "")
                    fixed_data[field] = fixed_list
        
        return fixed_data
    
    @staticmethod
    def fix_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in financial extraction data"""
        expected_schema = {
            "previous_rounds": List[str],
            "total_funding_raised": str,
            "last_valuation": str,
            "current_valuation": str,
            "investment_ask": str,
            "current_round_size": str,
            "use_of_funds": str,
            "ownership_percentages": Dict[str, str],
            "liquidation_preferences": str,
            "board_composition": str,
        }
        return DataValidator.validate_and_fix(data, expected_schema)
    
    @staticmethod
    def fix_market_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in market extraction data"""
        expected_schema = {
            "tam": str,
            "sam": str,
            "som": str,
            "market_growth_rate": str,
            "target_segments": List[str],
            "competitors": List[str],
            "competitive_advantages": List[str],
        }
        return DataValidator.validate_and_fix(data, expected_schema)
    
    @staticmethod
    def fix_company_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common issues in company extraction data"""
        expected_schema = {
            "company_name": str,
            "mission": str,
            "business_model": str,
            "products": List[str],
            "value_proposition": str,
            "go_to_market": str,
            "funding_stage": str,
            "current_round_details": str,
        }
        return DataValidator.validate_and_fix(data, expected_schema)

