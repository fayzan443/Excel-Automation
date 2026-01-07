"""
API routes for file upload and processing.
Handles file uploads, validation, and data cleaning.
"""
import time
from fastapi import APIRouter, UploadFile, HTTPException, status, Depends, File, Form
from typing import Dict, Any, List, Optional
import pandas as pd
import io
import os
import json

from app.utils.file_handlers import FileHandler
from app.services.data_cleaning_service import DataCleaner, CleaningOptions
from app.services.calculations_service import DataFrameCalculator, CalculationRule as CalculationRuleModel
from app.services.pivot_service import PivotService, PivotConfig
from app.core.schemas.file_schemas import (
    FileMetadata, 
    FileResponse, 
    FileUploadRequest,
    CleaningOptions as CleaningOptionsSchema,
    CalculationRule,
    CalculationCondition
)
import uuid

# Import the router from __init__.py to avoid circular imports
router = APIRouter()

# Custom JSON decoder for handling form data with JSON
def parse_json_field(json_str: str) -> Dict[str, Any]:
    """Parse a JSON string from form data."""
    try:
        return json.loads(json_str) if json_str else {}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in cleaning_options: {str(e)}"
        )

@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_200_OK)
async def upload_file(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    cleaning_options: Optional[str] = Form(None, description="JSON string of cleaning options")
) -> FileResponse:
    """
    Upload and process an Excel or CSV file with optional data cleaning.
    """
    start_time = time.time()
    
    try:
        # Check if file is empty
        if file.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
            
        # Parse cleaning options and calculation rules if provided
        cleaning_opts = None
        calculation_rules = None
        
        if cleaning_options:
            try:
                request_data = parse_json_field(cleaning_options)
                
                if 'cleaning_options' in request_data:
                    cleaning_opts = CleaningOptions(**request_data['cleaning_options'])
                
                if 'calculations' in request_data and request_data['calculations']:
                    calculation_rules = []
                    for rule in request_data['calculations']:
                        if 'condition' in rule and rule['condition']:
                            rule['condition'] = CalculationCondition(**rule['condition'])
                        calculation_rules.append(CalculationRule(**rule))
                        
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid request data: {str(e)}"
                )
        
        # Read file content
        content = await file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Validate file extension
        if file_extension not in ['.xlsx', '.xls', '.csv']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported types: .xlsx, .xls, .csv"
            )
        
        # Process the file based on its type
        sheets = {}
        try:
            if file_extension == '.csv':
                df = pd.read_csv(io.BytesIO(content))
                sheets = {'Sheet1': df}
            else:
                excel_file = pd.ExcelFile(io.BytesIO(content))
                for sheet in excel_file.sheet_names:
                    if sheet_name and sheet != sheet_name:
                        continue
                    sheets[sheet] = excel_file.parse(sheet_name=sheet)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )
        
        # Apply cleaning and calculations
        cleaning_operations = []
        calculation_results = {}
        for sheet_name, df in sheets.items():
            # Cleaning
            if cleaning_opts:
                cleaner = DataCleaner(df)
                cleaner.clean(cleaning_opts)
                sheets[sheet_name] = cleaner.get_cleaned_data()
                cleaning_operations.extend(cleaner.get_applied_operations())
            
            # Calculations
            if calculation_rules:
                try:
                    calculator = DataFrameCalculator(sheets[sheet_name])
                    result = calculator.apply_calculations(calculation_rules)
                    
                    if not result.success:
                        raise ValueError(f"Error in sheet '{sheet_name}': {result.error}")
                    
                    sheets[sheet_name] = result.result_df
                    calculation_results[sheet_name] = {
                        'success': True,
                        'columns_added': result.columns_added,
                        'message': result.message
                    }
                except Exception as e:
                    calculation_results[sheet_name] = {
                        'success': False,
                        'error': str(e),
                        'message': f"Error applying calculations: {str(e)}"
                    }
        
        # Prepare response data
        file_metadata = FileMetadata(
            file_name=file.filename,
            file_extension=file_extension,
            file_size=file.size,
            sheet_names=list(sheets.keys()),
            cleaning_applied=bool(cleaning_opts),
            cleaning_operations=cleaning_operations,
            sheets={
                name: {
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                    "sample_data": df.head(5).to_dict(orient='records')
                }
                for name, df in sheets.items()
            }
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return FileResponse.from_success(
            message="File processed successfully",
            metadata=file_metadata,
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        return FileResponse.from_error(
            message="An unexpected error occurred",
            error_details={"error": str(e)},
            processing_time_ms=processing_time_ms
        )
