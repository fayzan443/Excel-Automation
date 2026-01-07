"""
Unit tests for data cleaning functionality.
"""
import pytest
import pandas as pd
import numpy as np
from app.services.data_cleaning import DataCleaningService

class TestDataCleaningService:
    """Test cases for DataCleaningService."""
    
    def test_remove_duplicates(self, sample_data):
        """Test removing duplicate rows."""
        # Arrange
        df = sample_data['sales'].copy()
        # Add duplicate row
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        
        # Act
        cleaned_df = DataCleaningService.remove_duplicates(df)
        
        # Assert
        assert len(cleaned_df) == len(df) - 1
        assert cleaned_df.duplicated().sum() == 0
        
    def test_handle_missing_values(self, sample_data):
        """Test handling missing values."""
        # Arrange
        df = sample_data['sales'].copy()
        # Add some missing values
        df.loc[0, 'quantity'] = np.nan
        df.loc[1, 'price'] = None
        
        # Act - Test with different strategies
        filled_mean = DataCleaningService.handle_missing_values(
            df, strategy='mean', columns=['quantity']
        )
        filled_zero = DataCleaningService.handle_missing_values(
            df, strategy='constant', fill_value=0, columns=['price']
        )
        
        # Assert
        assert not filled_mean['quantity'].isna().any()
        assert not filled_zero['price'].isna().any()
        assert filled_zero.loc[1, 'price'] == 0
        
    def test_convert_dtypes(self, sample_data):
        """Test converting data types."""
        # Arrange
        df = sample_data['sales'].copy()
        # Convert numeric to string
        df['quantity'] = df['quantity'].astype(str)
        
        # Act
        converted = DataCleaningService.convert_dtypes(
            df, 
            dtypes={'quantity': 'int64', 'price': 'float32'}
        )
        
        # Assert
        assert pd.api.types.is_integer_dtype(converted['quantity'])
        assert pd.api.types.is_float_dtype(converted['price'])
        
    def test_clean_column_names(self, sample_data):
        """Test cleaning column names."""
        # Arrange
        df = sample_data['sales'].copy()
        df.columns = ['Date', 'Product Name', 'Category ', ' Qty ', ' Price ($) ', ' Discount%']
        
        # Act
        cleaned = DataCleaningService.clean_column_names(df)
        
        # Assert
        expected_columns = ['date', 'product_name', 'category', 'qty', 'price_usd', 'discount_pct']
        assert list(cleaned.columns) == expected_columns
