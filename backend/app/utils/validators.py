"""
Validation utilities for Excel-Cleaner.
Handles data validation and type checking.
"""
import re
from typing import Any, Dict, List, Optional, Union, Tuple, Type, Callable
import pandas as pd
import numpy as np
from datetime import datetime

class DataValidator:
    """Handles data validation and type checking."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if a string is a valid email address."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Check if a string is a valid phone number."""
        if not phone or not isinstance(phone, str):
            return False
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Check if it's a valid length (e.g., 10 digits for US numbers)
        return len(digits) >= 10
    
    @staticmethod
    def is_valid_date(date_str: str, date_format: str = '%Y-%m-%d') -> bool:
        """Check if a string is a valid date in the specified format."""
        if not date_str or not isinstance(date_str, str):
            return False
        try:
            datetime.strptime(date_str, date_format)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_numeric(value: Any) -> bool:
        """Check if a value is numeric (int, float, or numeric string)."""
        if value is None:
            return False
        if isinstance(value, (int, float, np.number)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        return False
    
    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame,
        schema: Dict[str, Tuple[Type, List[Callable]]]
    ) -> Dict[str, List[str]]:
        """
        Validate a DataFrame against a schema.
        
        Args:
            df: Input DataFrame
            schema: Dictionary mapping column names to (type, [validators]) tuples
                   Example: {'email': (str, [is_valid_email]), 'age': (int, [])}
                   
        Returns:
            Dictionary mapping column names to lists of error messages
        """
        errors = {col: [] for col in schema}
        
        for col, (expected_type, validators) in schema.items():
            if col not in df.columns:
                errors[col].append("Column not found in DataFrame")
                continue
                
            # Check type
            if expected_type is not None:
                for i, value in enumerate(df[col]):
                    if pd.isna(value):
                        continue
                    if not isinstance(value, expected_type) and not (
                        expected_type == float and isinstance(value, (int, np.integer))
                    ):
                        errors[col].append(
                            f"Row {i}: Expected {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            
            # Run validators
            for validator in validators:
                for i, value in enumerate(df[col]):
                    if pd.isna(value):
                        continue
                    try:
                        if not validator(value):
                            errors[col].append(
                                f"Row {i}: Validation failed for {validator.__name__}"
                            )
                    except Exception as e:
                        errors[col].append(
                            f"Row {i}: Error in validator {validator.__name__}: {str(e)}"
                        )
        
        # Remove columns with no errors
        return {k: v for k, v in errors.items() if v}
    
    @staticmethod
    def check_missing_values(df: pd.DataFrame) -> Dict[str, int]:
        """
        Count missing values in each column of a DataFrame.
        
        Returns:
            Dictionary mapping column names to counts of missing values
        """
        if not isinstance(df, pd.DataFrame):
            return {}
        return df.isna().sum().to_dict()
    
    @staticmethod
    def check_duplicates(df: pd.DataFrame, subset: List[str] = None) -> int:
        """
        Count duplicate rows in a DataFrame.
        
        Args:
            df: Input DataFrame
            subset: Columns to consider when identifying duplicates
            
        Returns:
            Number of duplicate rows
        """
        if not isinstance(df, pd.DataFrame):
            return 0
        return df.duplicated(subset=subset).sum()
