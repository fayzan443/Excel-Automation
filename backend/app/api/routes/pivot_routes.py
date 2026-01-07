"""
API routes for pivot table operations.
Handles generation of pivot tables from processed data.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List, Optional
import pandas as pd
import json

from app.services.pivot_service import PivotService, PivotConfig
from app.core.schemas.file_schemas import FileResponse

# Import the router from __init__.py to avoid circular imports
router = APIRouter()

# In-memory storage for processed DataFrames (in production, use a proper cache/database)
_data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}

@router.post("/pivot/{file_id}", response_model=FileResponse, status_code=status.HTTP_200_OK)
async def create_pivot(
    file_id: str,
    pivot_configs: List[Dict[str, Any]],
    sheet_name: Optional[str] = None
) -> FileResponse:
    """
    Generate pivot tables for the specified file.
    
    Args:
        file_id: ID of the previously processed file
        pivot_configs: List of pivot table configurations
        sheet_name: Optional specific sheet to process (for Excel files)
        
    Returns:
        FileResponse with pivot table results
    """
    try:
        # Check if we have data for this file_id
        if file_id not in _data_cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for file_id: {file_id}"
            )
        
        # Get the appropriate sheet
        sheets = _data_cache[file_id]
        
        if sheet_name and sheet_name not in sheets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sheet '{sheet_name}' not found in file"
            )
        
        # Process each requested sheet (or just the specified one)
        results = {}
        
        for current_sheet_name, df in sheets.items():
            if sheet_name and current_sheet_name != sheet_name:
                continue
                
            sheet_results = []
            
            # Apply each pivot configuration
            for i, config in enumerate(pivot_configs, 1):
                try:
                    # Validate and parse the config
                    pivot_config = PivotConfig(**config)
                    
                    # Generate the pivot table
                    result = PivotService.create_pivot(df, pivot_config)
                    
                    # Store the result with a reference name or index
                    pivot_name = f"pivot_{i}"
                    sheet_results.append({
                        "name": pivot_name,
                        "success": result["success"],
                        "data": result["data"],
                        "config": result["config"],
                        "error": result.get("error"),
                        "message": result.get("message")
                    })
                    
                except Exception as e:
                    sheet_results.append({
                        "name": f"pivot_{i}",
                        "success": False,
                        "error": "Invalid pivot configuration",
                        "message": str(e)
                    })
            
            results[current_sheet_name] = sheet_results
        
        return FileResponse(
            success=True,
            message=f"Generated {len(pivot_configs)} pivot table(s)",
            data={
                "file_id": file_id,
                "pivot_tables": results,
                "sheet_name": sheet_name if sheet_name else "all"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating pivot tables: {str(e)}"
        )

def cache_data(file_id: str, sheets: Dict[str, pd.DataFrame]) -> None:
    """
    Cache processed data for pivot table generation.
    
    Args:
        file_id: Unique identifier for the file
        sheets: Dictionary of sheet names to DataFrames
    """
    _data_cache[file_id] = sheets
    
    # Simple cache management (optional)
    if len(_data_cache) > 10:  # Keep only the last 10 files in cache
        oldest_key = next(iter(_data_cache))
        _data_cache.pop(oldest_key, None)
