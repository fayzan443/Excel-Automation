"""
Unit tests for pivot table functionality.
"""
import pytest
import pandas as pd
import numpy as np
from app.services.pivot_service import PivotService, PivotConfig

class TestPivotService:
    """Test cases for PivotService."""
    
    def test_create_pivot_basic(self, sample_data):
        """Test basic pivot table creation."""
        # Arrange
        df = sample_data['sales'].copy()
        config = PivotConfig(
            index=['category'],
            values=['quantity', 'price'],
            aggfunc='sum'
        )
        
        # Act
        result = PivotService.create_pivot(df, config)
        
        # Assert
        assert result['success'] is True
        assert 'data' in result
        assert 'category' in result['data']
        assert 'quantity' in result['data']
        assert 'price' in result['data']
        
    def test_pivot_with_margins(self, sample_data):
        """Test pivot table with margins."""
        # Arrange
        df = sample_data['sales'].copy()
        config = PivotConfig(
            index=['category'],
            values=['quantity'],
            aggfunc='sum',
            margins=True,
            margins_name='Total'
        )
        
        # Act
        result = PivotService.create_pivot(df, config)
        
        # Assert
        assert result['success'] is True
        assert 'Total' in result['data']['quantity']
        
    def test_pivot_with_multiple_aggregations(self, sample_data):
        """Test pivot table with multiple aggregation functions."""
        # Arrange
        df = sample_data['sales'].copy()
        config = PivotConfig(
            index=['category'],
            columns=['product'],
            values=['quantity'],
            aggfunc={
                'quantity': ['sum', 'mean', 'count']
            }
        )
        
        # Act
        result = PivotService.create_pivot(df, config)
        
        # Assert
        assert result['success'] is True
        assert 'sum' in str(result['data'])
        assert 'mean' in str(result['data'])
        assert 'count' in str(result['data'])
        
    def test_pivot_with_missing_columns(self, sample_data):
        """Test pivot with non-existent columns."""
        # Arrange
        df = sample_data['sales'].copy()
        config = PivotConfig(
            index=['nonexistent_column'],
            values=['quantity']
        )
        
        # Act
        result = PivotService.create_pivot(df, config)
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
        assert 'nonexistent_column' in result['message']
        
    def test_pivot_with_empty_dataframe(self):
        """Test pivot with empty DataFrame."""
        # Arrange
        df = pd.DataFrame()
        config = PivotConfig(
            index=['category'],
            values=['quantity']
        )
        
        # Act
        result = PivotService.create_pivot(df, config)
        
        # Assert
        assert result['success'] is False
        assert 'empty' in result['message'].lower()
