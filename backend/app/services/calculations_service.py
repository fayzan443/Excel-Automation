"""
Calculation service for Excel-Cleaner.
Handles Excel-like calculations on pandas DataFrames.
"""
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator
from enum import Enum

class CalculationType(str, Enum):
    """Supported calculation types."""
    SUM = "sum"
    COUNT = "count"
    COUNTIF = "countif"
    SUMIF = "sumif"
    IF = "if"
    CUSTOM = "custom"

class CalculationRule(BaseModel):
    """Defines a single calculation rule."""
    name: str = Field(..., description="Name of the resulting column")
    operation: CalculationType = Field(..., description="Type of calculation to perform")
    columns: List[str] = Field(..., description="Source columns for the calculation")
    condition: Optional[Dict[str, Any]] = Field(
        None,
        description="Condition for conditional operations (for COUNTIF, SUMIF, IF)"
    )
    true_value: Any = Field(
        None,
        description="Value to use when condition is true (for IF operation)"
    )
    false_value: Any = Field(
        None,
        description="Value to use when condition is false (for IF operation)"
    )
    custom_function: Optional[str] = Field(
        None,
        description="Custom Python function as string (for CUSTOM operation)"
    )

    @validator('columns')
    def validate_columns(cls, v):
        if not v:
            raise ValueError("At least one column must be specified")
        return v

class CalculationResult(BaseModel):
    """Result of applying calculations to a DataFrame."""
    success: bool
    message: str
    columns_added: List[str] = []
    error: Optional[str] = None
    result_df: Optional[pd.DataFrame] = None

    model_config = {
        "arbitrary_types_allowed": True
    }

class DataFrameCalculator:
    """Handles Excel-like calculations on pandas DataFrames."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with a DataFrame to perform calculations on."""
        self.df = df.copy()
        self.original_columns = set(df.columns)
        self.applied_calculations: List[Dict[str, Any]] = []
    
    def apply_calculations(self, rules: List[CalculationRule]) -> CalculationResult:
        """
        Apply a list of calculation rules to the DataFrame.
        
        Args:
            rules: List of CalculationRule objects defining the calculations
            
        Returns:
            CalculationResult with the results and any errors
        """
        try:
            for rule in rules:
                self._apply_rule(rule)
                
            # Get only the newly added columns
            new_columns = list(set(self.df.columns) - self.original_columns)
            
            return CalculationResult(
                success=True,
                message=f"Successfully applied {len(rules)} calculation(s)",
                columns_added=new_columns,
                result_df=self.df
            )
            
        except Exception as e:
            return CalculationResult(
                success=False,
                message=f"Error applying calculations: {str(e)}",
                error=str(e)
            )
    
    def _apply_rule(self, rule: CalculationRule) -> None:
        """Apply a single calculation rule to the DataFrame."""
        if rule.operation == CalculationType.SUM:
            self._apply_sum(rule)
        elif rule.operation == CalculationType.COUNT:
            self._apply_count(rule)
        elif rule.operation == CalculationType.COUNTIF:
            self._apply_countif(rule)
        elif rule.operation == CalculationType.SUMIF:
            self._apply_sumif(rule)
        elif rule.operation == CalculationType.IF:
            self._apply_if(rule)
        elif rule.operation == CalculationType.CUSTOM:
            self._apply_custom(rule)
        else:
            raise ValueError(f"Unsupported operation: {rule.operation}")
    
    def _apply_sum(self, rule: CalculationRule) -> None:
        """Apply SUM operation: Sum values across specified columns."""
        self._validate_columns_exist(rule.columns)
        self.df[rule.name] = self.df[rule.columns].sum(axis=1)
        self._log_operation(rule, f"Sum of columns: {', '.join(rule.columns)}")
    
    def _apply_count(self, rule: CalculationRule) -> None:
        """Apply COUNT operation: Count non-null values across specified columns."""
        self._validate_columns_exist(rule.columns)
        self.df[rule.name] = self.df[rule.columns].count(axis=1)
        self._log_operation(rule, f"Count of non-null values in columns: {', '.join(rule.columns)}")
    
    def _apply_countif(self, rule: CalculationRule) -> None:
        """Apply COUNTIF operation: Count values matching the condition."""
        if not rule.condition:
            raise ValueError("Condition is required for COUNTIF operation")
            
        column = rule.columns[0]  # COUNTIF works on a single column
        self._validate_columns_exist([column])
        
        # Parse condition (e.g., {"operator": ">", "value": 10})
        condition = self._parse_condition(column, rule.condition)
        self.df[rule.name] = np.where(condition, 1, 0).sum(axis=1)
        
        self._log_operation(
            rule, 
            f"Count of values in '{column}' where {self._format_condition(rule.condition)}"
        )
    
    def _apply_sumif(self, rule: CalculationRule) -> None:
        """Apply SUMIF operation: Sum values where condition is true."""
        if len(rule.columns) != 2:
            raise ValueError("SUMIF requires exactly two columns: [condition_column, sum_column]")
            
        if not rule.condition:
            raise ValueError("Condition is required for SUMIF operation")
            
        cond_col, sum_col = rule.columns
        self._validate_columns_exist([cond_col, sum_col])
        
        # Parse condition
        condition = self._parse_condition(cond_col, rule.condition)
        self.df[rule.name] = np.where(condition, self.df[sum_col], 0)
        
        self._log_operation(
            rule,
            f"Sum of '{sum_col}' where '{cond_col}' {self._format_condition(rule.condition)}"
        )
    
    def _apply_if(self, rule: CalculationRule) -> None:
        """Apply IF operation: Conditional value assignment."""
        if not rule.condition:
            raise ValueError("Condition is required for IF operation")
            
        column = rule.columns[0]  # IF works on a single column
        self._validate_columns_exist([column])
        
        # Parse condition
        condition = self._parse_condition(column, rule.condition)
        self.df[rule.name] = np.where(
            condition,
            rule.true_value,
            rule.false_value
        )
        
        self._log_operation(
            rule,
            f"IF '{column}' {self._format_condition(rule.condition)} "
            f"THEN {rule.true_value} ELSE {rule.false_value}"
        )
    
    def _apply_custom(self, rule: CalculationRule) -> None:
        """Apply a custom calculation using a Python expression."""
        if not rule.custom_function:
            raise ValueError("Custom function is required for CUSTOM operation")
            
        try:
            # This is a simple implementation - in production, you'd want to add
            # security measures to prevent arbitrary code execution
            local_vars = {'df': self.df, 'np': np, 'pd': pd}
            exec(f"result = {rule.custom_function}", globals(), local_vars)
            self.df[rule.name] = local_vars['result']
            
            self._log_operation(
                rule,
                f"Applied custom function: {rule.custom_function}"
            )
            
        except Exception as e:
            raise ValueError(f"Error in custom function: {str(e)}")
    
    def _parse_condition(self, column: str, condition: Dict[str, Any]) -> pd.Series:
        """Parse a condition into a boolean Series."""
        if not all(k in condition for k in ['operator', 'value']):
            raise ValueError("Condition must include 'operator' and 'value'")
            
        op = condition['operator']
        value = condition['value']
        
        if op == '==':
            return self.df[column] == value
        elif op == '!=':
            return self.df[column] != value
        elif op == '>':
            return self.df[column] > value
        elif op == '>=':
            return self.df[column] >= value
        elif op == '<':
            return self.df[column] < value
        elif op == '<=':
            return self.df[column] <= value
        elif op == 'in':
            return self.df[column].isin(value)
        elif op == 'contains':
            return self.df[column].astype(str).str.contains(str(value), na=False)
        else:
            raise ValueError(f"Unsupported operator: {op}")
    
    def _format_condition(self, condition: Dict[str, Any]) -> str:
        """Format a condition dictionary as a readable string."""
        if not condition:
            return ""
        return f"{condition.get('operator', '?')} {condition.get('value', '?')}"
    
    def _validate_columns_exist(self, columns: List[str]) -> None:
        """Check if all specified columns exist in the DataFrame."""
        missing = [col for col in columns if col not in self.df.columns]
        if missing:
            raise ValueError(f"Columns not found: {', '.join(missing)}")
    
    def _log_operation(self, rule: CalculationRule, details: str) -> None:
        """Log an applied calculation operation."""
        self.applied_calculations.append({
            "name": rule.name,
            "operation": rule.operation,
            "details": details,
            "columns": rule.columns
        })
