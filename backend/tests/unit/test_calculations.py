"""
Unit tests for data calculations and transformations.
"""
import pytest
import pandas as pd
import numpy as np
from app.services.calculations import CalculationService

class TestCalculationService:
    """Test cases for CalculationService."""
    
    def test_calculate_columns(self, sample_data):
        """Test calculating new columns."""
        # Arrange
        df = sample_data['sales'].copy()
        calculations = [
            {"column": "total", "formula": "quantity * price * (1 - discount)"},
            {"column": "is_high_value", "formula": "total > 2000"}
        ]
        
        # Act
        result = CalculationService.calculate_columns(df, calculations)
        
        # Assert
        expected_total = df['quantity'] * df['price'] * (1 - df['discount'])
        pd.testing.assert_series_equal(
            result['total'].round(2), 
            expected_total.round(2),
            check_names=False
        )
        assert 'is_high_value' in result.columns
        assert result['is_high_value'].dtype == bool
        
    def test_apply_filters(self, sample_data):
        """Test applying filters to data."""
        # Arrange
        df = sample_data['sales'].copy()
        filters = [
            {"column": "quantity", "operator": ">", "value": 15},
            {"column": "category", "operator": "==", "value": "X"}
        ]
        
        # Act
        filtered = CalculationService.apply_filters(df, filters)
        
        # Assert
        expected = df[(df['quantity'] > 15) & (df['category'] == 'X')]
        pd.testing.assert_frame_equal(filtered, expected)
        
    def test_aggregate_data(self, sample_data):
        """Test data aggregation."""
        # Arrange
        df = sample_data['sales'].copy()
        aggregations = {
            'quantity': 'sum',
            'price': ['mean', 'max']
        }
        
        # Act
        result = CalculationService.aggregate_data(
            df, 
            group_by=['category'],
            aggregations=aggregations
        )
        
        # Assert
        expected = df.groupby('category').agg({
            'quantity': 'sum',
            'price': ['mean', 'max']
        })
        pd.testing.assert_frame_equal(result, expected)
        
    def test_pivot_table(self, sample_data):
        """Test pivot table creation."""
        # Arrange
        df = sample_data['sales'].copy()
        
        # Act
        pivot = CalculationService.create_pivot(
            df,
            index=['category'],
            columns=['product'],
            values=['quantity'],
            aggfunc='sum'
        )
        
        # Assert
        expected = pd.pivot_table(
            df,
            index=['category'],
            columns=['product'],
            values=['quantity'],
            aggfunc='sum'
        )
        pd.testing.assert_frame_equal(pivot, expected)
