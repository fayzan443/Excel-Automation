"""
API routes for chart generation.
Handles creation of various chart types from processed data.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import json

from app.services.visualization import VisualizationService, ChartConfig
from app.core.schemas.file_schemas import FileResponse

# Import the router from __init__.py to avoid circular imports
router = APIRouter()

# In-memory storage for processed DataFrames (shared with other routes)
from .pivot_routes import _data_cache

# Initialize the visualization service
viz_service = VisualizationService()

@router.post("/chart/{file_id}", response_model=FileResponse, status_code=status.HTTP_200_OK)
async def create_chart(
    file_id: str,
    chart_configs: List[Dict[str, Any]],
    sheet_name: Optional[str] = None
) -> FileResponse:
    """
    Generate one or more charts for the specified file.
    
    Args:
        file_id: ID of the previously processed file
        chart_configs: List of chart configurations
        sheet_name: Optional specific sheet to process (for Excel files)
        
    Returns:
        FileResponse with chart image data in base64 format
        
    Example request body:
    [
        {
            "chart_type": "bar",
            "x": "category",
            "y": "value",
            "title": "Sales by Category",
            "xlabel": "Categories",
            "ylabel": "Sales Amount"
        },
        {
            "chart_type": "pie",
            "y": "value",
            "x": "category",
            "title": "Sales Distribution"
        }
    ]
    """
    try:
        # Check if we have data for this file_id
        if file_id not in _data_cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for file_id: {file_id}"
            )
        
        # Get the appropriate sheet(s)
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
            
            # Generate each requested chart
            for i, config in enumerate(chart_configs, 1):
                try:
                    # Create the chart
                    img_data = viz_service.create_chart(df, config)
                    
                    # Store the result with a reference name
                    chart_name = f"chart_{i}"
                    sheet_results.append({
                        "name": chart_name,
                        "type": config.get("chart_type"),
                        "image_data": f"data:image/png;base64,{img_data}",
                        "config": config,
                        "success": True
                    })
                    
                except Exception as e:
                    sheet_results.append({
                        "name": f"chart_{i}",
                        "type": config.get("chart_type") if isinstance(config, dict) else "unknown",
                        "success": False,
                        "error": str(e),
                        "config": config
                    })
            
            results[current_sheet_name] = sheet_results
        
        return FileResponse(
            success=True,
            message=f"Generated {sum(len(charts) for charts in results.values())} chart(s)",
            data={
                "file_id": file_id,
                "charts": results,
                "sheet_name": sheet_name if sheet_name else "all"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating charts: {str(e)}"
        )
