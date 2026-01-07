"""
Export Service for Excel-Cleaner.
Handles exporting data and charts to various file formats.
"""
from io import BytesIO
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import matplotlib.pyplot as plt
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet
import pdfkit
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import base64
import os
import tempfile

from app.services.visualization import VisualizationService

class ExportService:
    """
    Service for exporting data and charts to various file formats.
    
    This service provides methods to export data to Excel and PDF formats,
    with support for including charts and multiple sheets.
    """
    
    def __init__(self):
        self.viz_service = VisualizationService()
    
    def to_excel(
        self,
        data: Dict[str, pd.DataFrame],
        charts_config: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Export data to an Excel file with optional charts.
        
        Args:
            data: Dictionary of {sheet_name: DataFrame} pairs
            charts_config: Dictionary of {sheet_name: [chart_configs]} for charts to include
            output_path: Optional path to save the file. If None, returns BytesIO object.
            
        Returns:
            BytesIO object containing the Excel file if output_path is None, else None
            
        Example:
            data = {"Sheet1": df1, "Summary": df2}
            charts = {
                "Sheet1": [{"chart_type": "bar", "x": "category", "y": "value"}]
            }
            excel_data = export_service.to_excel(data, charts)
        """
        output = BytesIO()
        
        # Create Excel writer with XlsxWriter engine
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write each DataFrame to a different sheet
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get the xlsxwriter workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                # Auto-adjust column widths
                self._adjust_column_widths(worksheet, df)
                
                # Add charts if any
                if charts_config and sheet_name in charts_config:
                    self._add_charts_to_sheet(
                        workbook, worksheet, df, charts_config[sheet_name]
                    )
        
        # Reset buffer position to the beginning
        output.seek(0)
        
        # Save to file if output_path is provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())
            return None
            
        return output
    
    def to_pdf(
        self,
        data: Dict[str, pd.DataFrame],
        charts_config: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        output_path: Optional[str] = None,
        title: str = "Data Export"
    ) -> BytesIO:
        """
        Export data and charts to a PDF file.
        
        Args:
            data: Dictionary of {sheet_name: DataFrame} pairs
            charts_config: Dictionary of {sheet_name: [chart_configs]} for charts to include
            output_path: Optional path to save the file. If None, returns BytesIO object.
            title: Title for the PDF document
            
        Returns:
            BytesIO object containing the PDF if output_path is None, else None
        """
        # Create a temporary directory for chart images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create PDF document
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72, leftMargin=72,
                topMargin=72, bottomMargin=72
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Add title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                alignment=1  # Center
            )
            elements.append(Paragraph(title, title_style))
            
            # Process each sheet
            for sheet_name, df in data.items():
                # Add sheet title
                sheet_title = Paragraph(f"<b>{sheet_name}</b>", styles['Heading2'])
                elements.append(sheet_title)
                elements.append(Spacer(1, 12))
                
                # Convert DataFrame to a list of lists for PDF table
                table_data = [df.columns.tolist()] + df.values.tolist()
                
                # Create table
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 24))
                
                # Add charts if any
                if charts_config and sheet_name in charts_config:
                    for chart_config in charts_config[sheet_name]:
                        try:
                            # Generate chart image
                            img_data = self.viz_service.create_chart(df, chart_config)
                            
                            # Save chart to temporary file
                            chart_title = chart_config.get('title', 'Chart')
                            chart_path = os.path.join(temp_dir, f"{chart_title}.png")
                            with open(chart_path, 'wb') as f:
                                f.write(base64.b64decode(img_data))
                            
                            # Add chart to PDF
                            chart_img = Image(chart_path, width=6*inch, height=4*inch)
                            elements.append(chart_img)
                            elements.append(Spacer(1, 12))
                            
                        except Exception as e:
                            elements.append(Paragraph(
                                f"Error generating chart: {str(e)}", 
                                styles['Italic']
                            ))
                
                # Add page break between sheets
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("-" * 50, styles['Normal']))
                elements.append(Spacer(1, 24))
            
            # Build the PDF
            doc.build(elements)
            
            # Reset buffer position
            buffer.seek(0)
            
            # Save to file if output_path is provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return None
                
            return buffer
    
    def _adjust_column_widths(self, worksheet: Worksheet, df: pd.DataFrame) -> None:
        """Auto-adjust column widths in the Excel sheet."""
        for idx, col in enumerate(df.columns):
            # Set column width based on max length of column header and content
            max_length = max(
                df[col].astype(str).apply(len).max(),  # Max length in column
                len(str(col))  # Length of column header
            )
            # Add a little extra space
            worksheet.set_column(idx, idx, min(max_length + 2, 50))
    
    def _add_charts_to_sheet(
        self,
        workbook: Workbook,
        worksheet: Worksheet,
        df: pd.DataFrame,
        chart_configs: List[Dict[str, Any]]
    ) -> None:
        """Add charts to an Excel worksheet."""
        for config in chart_configs:
            try:
                # Create a chart object based on type
                chart_type = config.get('chart_type', 'bar')
                
                if chart_type == 'bar':
                    chart = workbook.add_chart({'type': 'column'})
                elif chart_type == 'line':
                    chart = workbook.add_chart({'type': 'line'})
                elif chart_type == 'pie':
                    chart = workbook.add_chart({'type': 'pie'})
                else:
                    continue  # Skip unsupported chart types
                
                # Get column indices for x and y values
                x_col = df.columns.get_loc(config['x']) if 'x' in config else None
                y_cols = [df.columns.get_loc(y) for y in config['y']] if 'y' in config else []
                
                # Add data series to the chart
                if x_col is not None and y_cols:
                    for y_col in y_cols:
                        chart.add_series({
                            'name': [worksheet.name, 0, y_col + 1],
                            'categories': [worksheet.name, 1, x_col, len(df), x_col],
                            'values': [worksheet.name, 1, y_col + 1, len(df), y_col + 1],
                        })
                
                # Set chart title and axis labels
                chart.set_title({'name': config.get('title', '')})
                if x_col is not None:
                    chart.set_x_axis({'name': config.get('xlabel', '')})
                if y_cols:
                    chart.set_y_axis({'name': config.get('ylabel', '')})
                
                # Insert the chart into the worksheet
                worksheet.insert_chart('H2', chart, {'x_offset': 25, 'y_offset': 10})
                
            except Exception as e:
                # Log error but continue with next chart
                print(f"Error adding chart: {str(e)}")
                continue
