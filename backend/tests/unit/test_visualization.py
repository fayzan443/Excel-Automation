"""
Unit tests for visualization functionality.
"""
import pytest
import pandas as pd
import base64
from app.services.visualization import VisualizationService, ChartConfig

class TestVisualizationService:
    """Test cases for VisualizationService."""
    
    def test_create_bar_chart(self, sample_data):
        """Test creating a bar chart."""
        # Arrange
        service = VisualizationService()
        df = sample_data['sales'].groupby('category')['quantity'].sum().reset_index()
        config = ChartConfig(
            chart_type='bar',
            x='category',
            y='quantity',
            title='Test Bar Chart',
            xlabel='Categories',
            ylabel='Total Quantity'
        )
        
        # Act
        result = service.create_chart(df, config)
        
        # Assert
        assert isinstance(result, str)
        assert result.startswith('iVBOR')  # PNG base64 starts with this
        
    def test_create_line_chart(self, sample_data):
        """Test creating a line chart."""
        # Arrange
        service = VisualizationService()
        df = sample_data['sales'].groupby(['date', 'category'])['quantity'].sum().reset_index()
        config = ChartConfig(
            chart_type='line',
            x='date',
            y='quantity',
            title='Test Line Chart',
            xlabel='Date',
            ylabel='Quantity'
        )
        
        # Act
        result = service.create_chart(df, config)
        
        # Assert
        assert isinstance(result, str)
        assert result.startswith('iVBOR')
        
    def test_create_pie_chart(self, sample_data):
        """Test creating a pie chart."""
        # Arrange
        service = VisualizationService()
        df = sample_data['sales'].groupby('category')['quantity'].sum().reset_index()
        config = ChartConfig(
            chart_type='pie',
            y='quantity',
            x='category',
            title='Test Pie Chart'
        )
        
        # Act
        result = service.create_chart(df, config)
        
        # Assert
        assert isinstance(result, str)
        assert result.startswith('iVBOR')
        
    def test_invalid_chart_type(self, sample_data):
        """Test with invalid chart type."""
        # Arrange
        service = VisualizationService()
        df = sample_data['sales']
        
        # Act & Assert
        with pytest.raises(ValueError):
            config = ChartConfig(chart_type='invalid_type')
            service.create_chart(df, config)
            
    def test_missing_required_columns(self, sample_data):
        """Test with missing required columns."""
        # Arrange
        service = VisualizationService()
        df = sample_data['sales']
        
        # Missing y for bar chart
        with pytest.raises(ValueError):
            config = ChartConfig(chart_type='bar', x='category')
            service.create_chart(df, config)
            
        # Missing y for line chart
        with pytest.raises(ValueError):
            config = ChartConfig(chart_type='line', x='date')
            service.create_chart(df, config)
            
        # Missing y for pie chart
        with pytest.raises(ValueError):
            config = ChartConfig(chart_type='pie')
            service.create_chart(pd.DataFrame(), config)
