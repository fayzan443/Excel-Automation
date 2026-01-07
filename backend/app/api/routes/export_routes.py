"""
API routes for exporting data and charts to various file formats.
"""
from fastapi import APIRouter, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Optional, Literal
import pandas as pd
import io
import os
from datetime import datetime

from app.services.export_service import ExportService
from app.core.schemas.file_schemas import FileResponse

# Import the router from __init__.py to avoid circular imports
router = APIRouter()

# In-memory storage for processed DataFrames (shared with other routes)
from .pivot_routes import _data_cache

# Initialize the export service
export_service = ExportService()

@router.get("/export/{file_id}", response_class=StreamingResponse)
async def export_file(
    file_id: str,
    format: Literal['excel', 'pdf'] = 'excel',
    sheet_name: Optional[str] = None,
    include_charts: bool = False,
    charts_config: Optional[Dict[str, List[Dict[str, Any]]]] = None,
):
    """
    Export processed data to Excel or PDF format.
    
    Args:
        file_id: ID of the previously processed file
        format: Export format ('excel' or 'pdf')
        sheet_name: Optional specific sheet to export (default: all sheets)
        include_charts: Whether to include charts in the export
        charts_config: Configuration for charts to include
            
    Returns:
        StreamingResponse with the exported file
        
    Example:
        GET /api/export/123?format=excel
    """
    try:
        # Check if we have data for this file_id
        if file_id not in _data_cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for file_id: {file_id}"
            )
        
        # Get the data
        sheets = _data_cache[file_id]
        
        # Filter sheets if a specific sheet is requested
        if sheet_name:
            if sheet_name not in sheets:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sheet '{sheet_name}' not found in file"
                )
            sheets = {sheet_name: sheets[sheet_name]}
        
        # Generate a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{file_id}_{timestamp}.{format}"
        
        # Export based on format
        if format == 'excel':
            # Get charts config if needed
            charts = charts_config if (include_charts and charts_config) else None
            
            # Export to Excel
            excel_data = export_service.to_excel(sheets, charts)
            
            # Return the file as a streaming response
            return StreamingResponse(
                io.BytesIO(excel_data.getvalue()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        elif format == 'pdf':
            # Get charts config if needed
            charts = charts_config if (include_charts and charts_config) else None
            
            # Export to PDF
            pdf_data = export_service.to_pdf(
                sheets, 
                charts,
                title=f"Data Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Return the file as a streaming response
            return StreamingResponse(
                io.BytesIO(pdf_data.getvalue()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {format}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting file: {str(e)}"
        )

@router.post("/export/{file_id}/preview", response_model=FileResponse)
async def preview_export(
    file_id: str,
    format: Literal['excel', 'pdf'] = 'excel',
    sheet_name: Optional[str] = None,
    include_charts: bool = False,
    charts_config: Optional[Dict[str, List[Dict[str, Any]]]] = None,
):
    """
    Preview the export configuration before downloading.
    
    This endpoint returns information about what will be exported
    without actually generating the file.
    """
    try:
        # Check if we have data for this file_id
        if file_id not in _data_cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for file_id: {file_id}"
            )
        
        # Get the data
        sheets = _data_cache[file_id]
        
        # Filter sheets if a specific sheet is requested
        if sheet_name:
            if sheet_name not in sheets:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sheet '{sheet_name}' not found in file"
                )
            sheets = {sheet_name: sheets[sheet_name]}
        
        # Prepare response data
        preview_data = {
            "file_id": file_id,
            "format": format,
            "sheets": [],
            "total_rows": 0,
            "total_columns": 0
        }
        
        # Add sheet info
        for name, df in sheets.items():
            sheet_info = {
                "name": name,
                "rows": len(df),
                "columns": len(df.columns),
                "columns_list": df.columns.tolist()
            }
            
            # Add chart info if applicable
            if include_charts and charts_config and name in charts_config:
                sheet_info["charts"] = [
                    {"type": c.get("chart_type"), "title": c.get("title", "")} 
                    for c in charts_config[name]
                ]
            
            preview_data["sheets"].append(sheet_info)
            preview_data["total_rows"] += len(df)
            preview_data["total_columns"] = max(preview_data["total_columns"], len(df.columns))
        
        return FileResponse(
            success=True,
            message=f"Preview of {len(sheets)} sheet(s) to be exported as {format.upper()}",
            data=preview_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating export preview: {str(e)}"
        )
