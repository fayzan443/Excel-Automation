"""
Pydantic models for file processing API.
Defines request/response schemas for file operations.
"""
from typing import Dict, List, Optional, Any, Union, Literal, TypeVar, Generic
from enum import Enum
from pydantic import BaseModel, Field, validator, AnyUrl, HttpUrl
from datetime import datetime
from pydantic.generics import GenericModel

# Generic type for API responses
T = TypeVar('T')

class CalculationType(str, Enum):
    """Supported calculation types."""
    SUM = "sum"
    COUNT = "count"
    COUNTIF = "countif"
    SUMIF = "sumif"
    IF = "if"
    CUSTOM = "custom"

# Enums for validation
TextCaseOptions = Literal['upper', 'lower', 'title', None]
MissingValueHandling = Literal['keep', 'drop', 'fill']

class CleaningOptions(BaseModel):
    """Options for data cleaning operations."""
    remove_duplicates: bool = Field(
        default=False,
        description="Whether to remove duplicate rows"
    )
    handle_missing: MissingValueHandling = Field(
        default="keep",
        description="How to handle missing values: 'drop' to remove, 'fill' to fill with a value, 'keep' to leave as is"
    )
    fill_value: Optional[Any] = Field(
        default=None,
        description="Value to use when filling missing values (required if handle_missing is 'fill')"
    )
    trim_whitespace: bool = Field(
        default=True,
        description="Whether to trim whitespace from string values"
    )
    text_case: Optional[TextCaseOptions] = Field(
        default=None,
        description="Convert text to specified case: 'upper', 'lower', 'title', or None to keep original"
    )
    date_columns: List[str] = Field(
        default_factory=list,
        description="List of column names to parse as dates"
    )
    date_format: Optional[str] = Field(
        default=None,
        description="Format string for parsing dates (e.g., '%Y-%m-%d')"
    )

    @validator('fill_value', always=True)
    def validate_fill_value(cls, v, values):
        if values.get('handle_missing') == 'fill' and v is None:
            raise ValueError("fill_value is required when handle_missing is 'fill'")
        return v

class FileMetadata(BaseModel):
    """Metadata for an uploaded file."""
    file_name: str = Field(..., description="Original name of the uploaded file")
    file_extension: str = Field(..., description="File extension (e.g., .xlsx, .csv)")
    file_size: int = Field(..., description="Size of the file in bytes")
    sheet_names: List[str] = Field(..., description="List of sheet names in the file")
    sheets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadata for each sheet in the file"
    )
    cleaning_applied: bool = Field(
        default=False,
        description="Whether data cleaning was applied"
    )
    cleaning_operations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of cleaning operations that were applied"
    )

class CalculationCondition(BaseModel):
    """Condition for conditional calculations."""
    operator: str = Field(..., description="Comparison operator (==, !=, >, >=, <, <=, in, contains)")
    value: Any = Field(..., description="Value to compare against")

class CalculationRule(BaseModel):
    """Defines a single calculation to be applied to the data."""
    name: str = Field(..., description="Name of the resulting column")
    operation: CalculationType = Field(..., description="Type of calculation to perform")
    columns: List[str] = Field(..., description="Source columns for the calculation")
    condition: Optional[CalculationCondition] = Field(
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

class FileUploadRequest(BaseModel):
    """Request model for file upload with processing options."""
    sheet_name: Optional[str] = Field(
        None,
        description="Specific sheet name to process (for Excel files only)"
    )
    cleaning_options: Optional[CleaningOptions] = Field(
        None,
        description="Options for data cleaning"
    )
    calculations: Optional[List[CalculationRule]] = Field(
        None,
        description="List of calculations to apply to the data"
    )

class FileResponse(BaseModel):
    """Standard response for file operations."""
    success: bool = Field(..., description="Indicates if the operation was successful")
    message: str = Field(..., description="Human-readable message about the operation result")
    data: Optional[FileMetadata] = Field(
        None,
        description="File metadata if the operation was successful"
    )
    error: Optional[Dict[str, Any]] = Field(
        None,
        description="Error details if the operation failed"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process the request in milliseconds"
    )

    @classmethod
    def from_error(
        cls, 
        message: str, 
        error_details: Dict[str, Any] = None,
        processing_time_ms: float = None
    ) -> 'FileResponse':
        """Create an error response."""
        return cls(
            success=False,
            message=message,
            error=error_details or {},
            processing_time_ms=processing_time_ms
        )

    @classmethod
    def from_success(
        cls, 
        message: str, 
        metadata: FileMetadata = None,
        processing_time_ms: float = None
    ) -> 'FileResponse':
        """Create a success response with optional metadata."""
        return cls(
            success=True,
            message=message,
            data=metadata,
            processing_time_ms=processing_time_ms
        )
