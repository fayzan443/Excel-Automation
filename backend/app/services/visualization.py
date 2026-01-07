"""
Visualization service for Excel-Cleaner.
Handles generation of charts and plots from pandas DataFrames.

This module provides functionality to create various types of charts (bar, line, pie)
and return them as base64-encoded PNG images that can be embedded in web responses.
"""
from typing import Dict, Any, List, Optional, Union, Tuple, Literal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from pydantic import BaseModel, Field, validator

# Type aliases
ChartType = Literal['bar', 'line', 'pie']

class ChartConfig(BaseModel):
    """Configuration for generating a chart."""
    chart_type: ChartType = Field(..., description="Type of chart to generate")
    x: Optional[str] = Field(None, description="Column for x-axis")
    y: Optional[Union[str, List[str]]] = Field(None, description="Column(s) for y-axis")
    title: str = Field('', description="Chart title")
    xlabel: str = Field('', description="X-axis label")
    ylabel: str = Field('', description="Y-axis label")
    figsize: Optional[Tuple[int, int]] = Field(None, description="Figure size (width, height)")
    color: Optional[Union[str, List[str]]] = Field(None, description="Color(s) for the chart")
    legend: bool = Field(True, description="Whether to show legend")
    grid: bool = Field(True, description="Whether to show grid")
    
    # Additional parameters specific to chart types
    explode: Optional[List[float]] = Field(None, description="For pie charts: explode slices")
    autopct: Optional[str] = Field(None, description="For pie charts: format string for percentages")
    
    @validator('chart_type')
    def validate_chart_type(cls, v):
        valid_types = ['bar', 'line', 'pie']
        if v not in valid_types:
            raise ValueError(f"Invalid chart type. Must be one of: {', '.join(valid_types)}")
        return v
    
    @validator('y', pre=True)
    def validate_y(cls, v, values):
        if 'chart_type' in values and values['chart_type'] != 'pie' and v is None:
            raise ValueError("Y-axis must be specified for non-pie charts")
        return v

class VisualizationService:
    """
    Service for generating various types of charts from pandas DataFrames.
    
    This service provides methods to create bar, line, and pie charts with
    customizable appearance and styling. All charts are returned as base64-encoded
    PNG images that can be directly embedded in web responses.
    
    Example:
        service = VisualizationService()
        
        # Create a bar chart
        img_data = service.create_chart(
            df=my_dataframe,
            config=ChartConfig(
                chart_type='bar',
                x='category',
                y='value',
                title='My Bar Chart',
                xlabel='Categories',
                ylabel='Values'
            )
        )
    """
    
    def __init__(self):
        """Initialize the visualization service with default styles."""
        plt.style.use('seaborn')
        sns.set_palette('viridis')
        self.default_figsize = (10, 6)
    
    def create_bar_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        title: str = '',
        xlabel: str = '',
        ylabel: str = 'Value',
        figsize: Optional[Tuple[int, int]] = None,
        color: Optional[Union[str, List[str]]] = None,
        legend: bool = True,
        grid: bool = True,
        **kwargs
    ) -> str:
        """
        Create a bar plot and return as base64 encoded image.
        
        Args:
            df: Input DataFrame
            x: Column for x-axis (categorical data)
            y: Column(s) for y-axis (numeric data)
            title: Plot title
            xlabel: X-axis label (defaults to x column name)
            ylabel: Y-axis label
            figsize: Figure size (width, height)
            color: Color(s) for the bars (single color or list of colors)
            legend: Whether to show the legend
            grid: Whether to show grid lines
            **kwargs: Additional arguments to pass to matplotlib's bar function
            
        Returns:
            Base64 encoded PNG image string
            
        Raises:
            ValueError: If required columns are missing or invalid
        """
        # Validate input
        if x not in df.columns:
            raise ValueError(f"Column '{x}' not found in DataFrame")
            
        if isinstance(y, str):
            y = [y]
            
        for col in y:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame")
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=figsize or self.default_figsize)
        
        # Plot each y column
        for i, col in enumerate(y):
            if color and isinstance(color, list) and len(color) > i:
                c = color[i]
            elif color:
                c = color
            else:
                c = None
                
            ax.bar(
                df[x], 
                df[col], 
                label=col if len(y) > 1 else None,
                color=c,
                **kwargs
            )
        
        # Customize the plot
        ax.set_title(title or f"Bar Chart: {x} vs {', '.join(y)}")
        ax.set_xlabel(xlabel or x)
        ax.set_ylabel(ylabel)
        
        if legend and len(y) > 1:
            ax.legend()
            
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # Rotate x-tick labels if they're long
        if any(len(str(label)) > 10 for label in df[x]):
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_line_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        title: str = '',
        xlabel: str = '',
        ylabel: str = 'Value',
        figsize: Optional[Tuple[int, int]] = None,
        color: Optional[Union[str, List[str]]] = None,
        legend: bool = True,
        grid: bool = True,
        **kwargs
    ) -> str:
        """
        Create a line plot and return as base64 encoded image.
        
        Args:
            df: Input DataFrame
            x: Column for x-axis (typically time or ordered category)
            y: Column(s) for y-axis (can be a list for multiple lines)
            title: Plot title
            xlabel: X-axis label (defaults to x column name)
            ylabel: Y-axis label
            figsize: Figure size (width, height)
            color: Color(s) for the lines (single color or list of colors)
            legend: Whether to show the legend
            grid: Whether to show grid lines
            **kwargs: Additional arguments to pass to matplotlib's plot function
            
        Returns:
            Base64 encoded PNG image string
            
        Raises:
            ValueError: If required columns are missing or invalid
        """
        # Validate input
        if x not in df.columns:
            raise ValueError(f"Column '{x}' not found in DataFrame")
            
        if isinstance(y, str):
            y = [y]
            
        for col in y:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame")
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=figsize or self.default_figsize)
        
        # Plot each y column
        for i, col in enumerate(y):
            if color and isinstance(color, list) and len(color) > i:
                c = color[i]
            elif color:
                c = color
            else:
                c = None
                
            ax.plot(
                df[x], 
                df[col], 
                'o-',  # Marker and line style
                label=col if len(y) > 1 else None,
                color=c,
                **kwargs
            )
        
        # Customize the plot
        ax.set_title(title or f"Line Plot: {x} vs {', '.join(y)}")
        ax.set_xlabel(xlabel or x)
        ax.set_ylabel(ylabel)
        
        if legend and len(y) > 1:
            ax.legend()
            
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)
        
        # Rotate x-tick labels if they're long
        if any(len(str(label)) > 10 for label in df[x]):
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_pie_chart(
        self,
        df: pd.DataFrame,
        values: str,
        labels: Optional[str] = None,
        title: str = '',
        explode: Optional[List[float]] = None,
        autopct: Optional[str] = '%1.1f%%',
        figsize: Optional[Tuple[int, int]] = None,
        colors: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Create a pie chart and return as base64 encoded image.
        
        Args:
            df: Input DataFrame
            values: Column containing the values for the pie slices
            labels: Column containing the labels for the pie slices (defaults to index)
            title: Chart title
            explode: If not None, explode the specified slices
            autopct: Format string for percentage values
            figsize: Figure size (width, height)
            colors: Colors for the pie slices
            **kwargs: Additional arguments to pass to matplotlib's pie function
            
        Returns:
            Base64 encoded PNG image string
            
        Raises:
            ValueError: If required columns are missing or invalid
        """
        # Validate input
        if values not in df.columns:
            raise ValueError(f"Column '{values}' not found in DataFrame")
            
        if labels is not None and labels not in df.columns:
            raise ValueError(f"Label column '{labels}' not found in DataFrame")
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=figsize or self.default_figsize)
        
        # Prepare data
        values_data = df[values]
        labels_data = df[labels].values if labels is not None else df.index
        
        # Create the pie chart
        wedges, texts, autotexts = ax.pie(
            values_data,
            labels=labels_data if labels is not None else None,
            autopct=autopct,
            explode=explode,
            colors=colors,
            startangle=90,
            pctdistance=0.85,
            **kwargs
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        
        # Add title
        ax.set_title(title or f"Pie Chart: {values}")
        
        # Improve appearance
        plt.setp(autotexts, size=10, weight="bold")
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def create_chart(
        self,
        df: pd.DataFrame,
        config: Union[ChartConfig, Dict[str, Any]]
    ) -> str:
        """
        Create a chart based on the provided configuration.
        
        Args:
            df: Input DataFrame
            config: Either a ChartConfig object or a dictionary with chart configuration
            
        Returns:
            Base64 encoded PNG image string
            
        Raises:
            ValueError: If chart type is not supported or configuration is invalid
        """
        if not isinstance(config, ChartConfig):
            config = ChartConfig(**config)
        
        # Convert data to numeric where needed
        df = df.copy()
        
        # Handle different chart types
        if config.chart_type == 'bar':
            if not config.x or not config.y:
                raise ValueError("Both x and y must be specified for bar charts")
            return self.create_bar_plot(
                df=df,
                x=config.x,
                y=config.y,
                title=config.title,
                xlabel=config.xlabel,
                ylabel=config.ylabel,
                figsize=config.figsize,
                color=config.color,
                legend=config.legend,
                grid=config.grid
            )
            
        elif config.chart_type == 'line':
            if not config.x or not config.y:
                raise ValueError("Both x and y must be specified for line charts")
            return self.create_line_plot(
                df=df,
                x=config.x,
                y=config.y,
                title=config.title,
                xlabel=config.xlabel,
                ylabel=config.ylabel,
                figsize=config.figsize,
                color=config.color,
                legend=config.legend,
                grid=config.grid
            )
            
        elif config.chart_type == 'pie':
            if not config.y:
                raise ValueError("Y must be specified for pie charts")
            return self.create_pie_chart(
                df=df,
                values=config.y[0] if isinstance(config.y, list) else config.y,
                labels=config.x,
                title=config.title,
                explode=config.explode,
                autopct=config.autopct,
                figsize=config.figsize,
                colors=config.color if isinstance(config.color, list) else None
            )
            
        else:
            raise ValueError(f"Unsupported chart type: {config.chart_type}")
    
    def create_scatter_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        hue: Optional[str] = None,
        title: str = '',
        xlabel: str = '',
        ylabel: str = '',
        figsize: Tuple[int, int] = None,
        **kwargs
    ) -> str:
        """
        Create a scatter plot and return as base64 encoded image.
        
        Args:
            df: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            hue: Column to determine point colors
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size (width, height)
            **kwargs: Additional arguments to pass to seaborn.scatterplot()
            
        Returns:
            Base64 encoded image string
        """
        pass
    
    @staticmethod
    def _fig_to_base64(fig: plt.Figure) -> str:
        """
        Convert a matplotlib figure to a base64-encoded PNG image.
        
        Args:
            fig: Matplotlib figure to convert
            
        Returns:
            Base64-encoded string of the PNG image
        """
        try:
            img = BytesIO()
            # Use a white background
            fig.savefig(
                img, 
                format='png', 
                bbox_inches='tight',
                facecolor=fig.get_facecolor(),
                dpi=100,
                transparent=False
            )
            plt.close(fig)  # Close the figure to free memory
            return base64.b64encode(img.getvalue()).decode('utf-8')
        except Exception as e:
            plt.close(fig)  # Ensure figure is closed even if there's an error
            raise RuntimeError(f"Failed to convert figure to base64: {str(e)}")
