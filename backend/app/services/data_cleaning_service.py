"""
Data cleaning service for Excel-Cleaner.
Handles various data cleaning operations on pandas DataFrames.
"""
from typing import Dict, Any, List, Optional, Union, Callable
import pandas as pd
import re
from datetime import datetime
from pydantic import BaseModel, Field

class CleaningOptions(BaseModel):
    """Configuration options for data cleaning operations."""
    remove_duplicates: bool = Field(
        default=False,
        description="Remove duplicate rows from the DataFrame"
    )
    handle_missing: str = Field(
        default="keep",
        description="How to handle missing values: 'drop' to remove, 'fill' to fill with a value, 'keep' to leave as is"
    )
    fill_value: Any = Field(
        default=None,
        description="Value to use when filling missing values"
    )
    trim_whitespace: bool = Field(
        default=True,
        description="Trim whitespace from string columns"
    )
    text_case: Optional[str] = Field(
        default=None,
        description="Convert text case: 'upper', 'lower', 'title', or None to keep original"
    )
    date_columns: List[str] = Field(
        default_factory=list,
        description="List of column names that should be parsed as dates"
    )
    date_format: Optional[str] = Field(
        default=None,
        description="Format string for parsing dates (e.g., '%Y-%m-%d')"
    )

class DataCleaner:
    """Service class for performing data cleaning operations on DataFrames."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with a DataFrame to clean."""
        self.original_df = df
        self.cleaned_df = df.copy()
        self.applied_operations: List[Dict[str, Any]] = []
    
    def clean(self, options: CleaningOptions) -> 'DataCleaner':
        """
        Apply all specified cleaning operations to the DataFrame.
        
        Args:
            options: CleaningOptions object specifying which operations to perform
            
        Returns:
            self for method chaining
        """
        # Apply cleaning operations in a specific order
        if options.remove_duplicates:
            self._remove_duplicates()
            
        if options.handle_missing != "keep":
            self._handle_missing_values(options.handle_missing, options.fill_value)
            
        if options.trim_whitespace:
            self._trim_whitespace()
            
        if options.text_case:
            self._standardize_text_case(options.text_case)
            
        if options.date_columns:
            self._parse_dates(options.date_columns, options.date_format)
            
        return self
    
    def get_cleaned_data(self) -> pd.DataFrame:
        """Return the cleaned DataFrame."""
        return self.cleaned_df
    
    def get_applied_operations(self) -> List[Dict[str, Any]]:
        """Return a list of all cleaning operations that were applied."""
        return self.applied_operations
    
    def _log_operation(self, operation: str, details: Dict[str, Any] = None) -> None:
        """Log a cleaning operation that was performed."""
        self.applied_operations.append({
            "operation": operation,
            "details": details or {}
        })
    
    def _remove_duplicates(self) -> None:
        """Remove duplicate rows from the DataFrame."""
        initial_count = len(self.cleaned_df)
        self.cleaned_df = self.cleaned_df.drop_duplicates()
        removed_count = initial_count - len(self.cleaned_df)
        
        if removed_count > 0:
            self._log_operation(
                "remove_duplicates",
                {"rows_removed": removed_count}
            )
    
    def _handle_missing_values(self, method: str, fill_value: Any = None) -> None:
        """
        Handle missing values in the DataFrame.
        
        Args:
            method: 'drop' to remove rows with missing values, 'fill' to fill them
            fill_value: Value to use when filling missing values
        """
        if method == "drop":
            initial_count = len(self.cleaned_df)
            self.cleaned_df = self.cleaned_df.dropna()
            removed_count = initial_count - len(self.cleaned_df)
            
            if removed_count > 0:
                self._log_operation(
                    "drop_missing_values",
                    {"rows_removed": removed_count}
                )
                
        elif method == "fill" and fill_value is not None:
            fill_count = self.cleaned_df.isna().sum().sum()
            self.cleaned_df = self.cleaned_df.fillna(fill_value)
            
            if fill_count > 0:
                self._log_operation(
                    "fill_missing_values",
                    {"values_filled": fill_count, "fill_value": fill_value}
                )
    
    def _trim_whitespace(self) -> None:
        """Trim whitespace from string columns."""
        str_cols = self.cleaned_df.select_dtypes(include=['object']).columns
        
        for col in str_cols:
            self.cleaned_df[col] = self.cleaned_df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        
        if len(str_cols) > 0:
            self._log_operation("trim_whitespace")
    
    def _standardize_text_case(self, case: str) -> None:
        """
        Standardize text case in string columns.
        
        Args:
            case: 'upper', 'lower', or 'title'
        """
        str_cols = self.cleaned_df.select_dtypes(include=['object']).columns
        
        if case == "upper":
            for col in str_cols:
                self.cleaned_df[col] = self.cleaned_df[col].apply(
                    lambda x: x.upper() if isinstance(x, str) else x
                )
        elif case == "lower":
            for col in str_cols:
                self.cleaned_df[col] = self.cleaned_df[col].apply(
                    lambda x: x.lower() if isinstance(x, str) else x
                )
        elif case == "title":
            for col in str_cols:
                self.cleaned_df[col] = self.cleaned_df[col].apply(
                    lambda x: x.title() if isinstance(x, str) else x
                )
        
        if len(str_cols) > 0:
            self._log_operation("standardize_text_case", {"case": case})
    
    def _parse_dates(self, date_columns: List[str], date_format: str = None) -> None:
        """
        Parse specified columns as dates.
        
        Args:
            date_columns: List of column names to parse as dates
            date_format: Optional format string for parsing dates
        """
        if not date_columns:
            return
            
        date_columns = [col for col in date_columns if col in self.cleaned_df.columns]
        
        for col in date_columns:
            try:
                if date_format:
                    self.cleaned_df[col] = pd.to_datetime(
                        self.cleaned_df[col],
                        format=date_format,
                        errors='coerce'
                    )
                else:
                    self.cleaned_df[col] = pd.to_datetime(
                        self.cleaned_df[col],
                        infer_datetime_format=True,
                        errors='coerce'
                    )
            except Exception as e:
                self._log_operation(
                    "parse_dates_error",
                    {"column": col, "error": str(e)}
                )
        
        if date_columns:
            self._log_operation("parse_dates", {"columns": date_columns})
