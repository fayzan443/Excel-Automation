"""
Pivot table service for Excel-Cleaner.
Handles generation of pivot tables and summary views from pandas DataFrames.
"""
from typing import Dict, Any, List, Optional, Union, Literal, TypedDict
from enum import Enum
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator

# Type aliases
AggregationType = Literal['sum', 'count', 'mean', 'min', 'max', 'first', 'last', 'std', 'var']

class PivotConfig(BaseModel):
    """Configuration for generating a pivot table."""
    index: List[str] = Field(
        ...,
        description="Columns to use as index (rows) in the pivot table"
    )
    columns: Optional[List[str]] = Field(
        None,
        description="Columns to use as columns in the pivot table"
    )
    values: Optional[List[str]] = Field(
        None,
        description="Columns to aggregate. If None, all numeric columns not in index/columns will be used"
    )
    aggfunc: Union[AggregationType, Dict[str, Union[AggregationType, List[AggregationType]]]] = Field(
        'sum',
        description="Aggregation function(s) to apply. Can be a string for all values or a dict per column"
    )
    fill_value: Any = Field(
        None,
        description="Value to replace missing values with"
    )
    margins: bool = Field(
        False,
        description="Add all row/column totals"
    )
    margins_name: str = Field(
        'Total',
        description="Name of the row/column containing totals when margins=True"
    )

    @validator('index')
    def validate_index(cls, v):
        if not v:
            raise ValueError("At least one index column must be specified")
        return v
    
    @validator('aggfunc')
    def validate_aggfunc(cls, v):
        valid_aggs = ['sum', 'count', 'mean', 'min', 'max', 'first', 'last', 'std', 'var']
        
        if isinstance(v, str):
            if v not in valid_aggs:
                raise ValueError(f"Invalid aggregation function: {v}")
            return v
            
        if isinstance(v, dict):
            for col, func in v.items():
                if isinstance(func, str):
                    if func not in valid_aggs:
                        raise ValueError(f"Invalid aggregation function for column {col}: {func}")
                elif isinstance(func, list):
                    for f in func:
                        if f not in valid_aggs:
                            raise ValueError(f"Invalid aggregation function for column {col}: {f}")
            return v
            
        raise ValueError("aggfunc must be a string or a dictionary mapping columns to aggregation functions")

class PivotResult(TypedDict):
    """Result of a pivot table generation."""
    success: bool
    data: Dict[str, Any]
    config: Dict[str, Any]
    error: Optional[str]
    message: Optional[str]

class PivotService:
    """Service for generating pivot tables from pandas DataFrames."""
    
    @staticmethod
    def create_pivot(
        df: pd.DataFrame, 
        config: PivotConfig
    ) -> PivotResult:
        """
        Generate a pivot table from a DataFrame based on the provided configuration.
        
        Args:
            df: Input DataFrame
            config: Pivot configuration
            
        Returns:
            PivotResult containing the pivot table data or error information
        """
        try:
            # Validate columns exist in the DataFrame
            all_columns = set(df.columns)
            missing_columns = []
            
            # Check index columns
            for col in config.index:
                if col not in all_columns:
                    missing_columns.append(f"Index column not found: {col}")
            
            # Check pivot columns if specified
            if config.columns:
                for col in config.columns:
                    if col not in all_columns:
                        missing_columns.append(f"Column not found: {col}")
            
            # Check value columns if specified
            if config.values:
                for col in config.values:
                    if col not in all_columns:
                        missing_columns.append(f"Value column not found: {col}")
            
            if missing_columns:
                return PivotResult(
                    success=False,
                    data={},
                    config=config.dict(),
                    error="Column validation failed",
                    message=", ".join(missing_columns)
                )
            
            # Create the pivot table
            pivot_df = pd.pivot_table(
                data=df,
                index=config.index,
                columns=config.columns,
                values=config.values,
                aggfunc=config.aggfunc,
                fill_value=config.fill_value,
                margins=config.margins,
                margins_name=config.margins_name
            )
            
            # Convert the pivot table to a JSON-serializable format
            result = PivotService._pivot_to_dict(pivot_df)
            
            return PivotResult(
                success=True,
                data=result,
                config=config.dict(),
                message="Pivot table generated successfully"
            )
            
        except Exception as e:
            return PivotResult(
                success=False,
                data={},
                config=config.dict() if 'config' in locals() else {},
                error="Error generating pivot table",
                message=str(e)
            )
    
    @staticmethod
    def _pivot_to_dict(pivot_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Convert a pivot DataFrame to a JSON-serializable dictionary.
        Handles both single and multi-level indexes/columns.
        """
        # Reset index to include index columns in the output
        result_df = pivot_df.reset_index()
        
        # Convert to dictionary with proper handling of different data types
        data = []
        
        # Get column names (handling MultiIndex if present)
        if isinstance(result_df.columns, pd.MultiIndex):
            columns = [
                '.'.join(map(str, col)).strip('.')
                for col in result_df.columns
            ]
        else:
            columns = result_df.columns.tolist()
        
        # Convert each row to a dictionary
        for _, row in result_df.iterrows():
            row_dict = {}
            for col in columns:
                # Handle MultiIndex column access
                if isinstance(col, str) and '.' in col:
                    parts = col.split('.')
                    try:
                        value = row[tuple(parts)]
                    except (KeyError, TypeError):
                        value = row[col]
                else:
                    value = row[col]
                
                # Convert non-serializable types
                if pd.isna(value):
                    value = None
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    value = int(value)
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    value = float(value)
                
                row_dict[col] = value
            
            data.append(row_dict)
        
        return {
            "columns": columns,
            "data": data,
            "index_columns": pivot_df.index.names if hasattr(pivot_df.index, 'names') else [None],
            "column_levels": pivot_df.columns.names if hasattr(pivot_df.columns, 'names') else [None]
        }
