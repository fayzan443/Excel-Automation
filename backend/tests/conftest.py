"""
Pytest configuration and fixtures for testing the Excel-Cleaner backend.
"""
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

# Sample test data
@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        'sales': pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5).repeat(2),
            'product': ['A', 'B'] * 5,
            'category': ['X', 'Y'] * 5,
            'quantity': [10, 20, 15, 25, 30, 10, 40, 5, 20, 15],
            'price': [100, 200, 150, 250, 300, 100, 400, 50, 200, 150],
            'discount': [0.1, 0, 0.15, 0.2, 0.1, 0, 0.05, 0.1, 0, 0.15]
        }),
        'products': pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'category': ['X', 'Y', 'X'],
            'cost': [50, 100, 75],
            'in_stock': [True, True, False]
        })
    }

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

# Helper functions
def assert_dataframes_equal(df1, df2, **kwargs):
    """Assert that two DataFrames are equal, ignoring index and dtypes."""
    return pd.testing.assert_frame_equal(
        df1.reset_index(drop=True), 
        df2.reset_index(drop=True),
        check_dtype=False,
        **kwargs
    )

def assert_series_equal(s1, s2, **kwargs):
    """Assert that two Series are equal, ignoring index and dtypes."""
    return pd.testing.assert_series_equal(
        s1.reset_index(drop=True),
        s2.reset_index(drop=True),
        check_dtype=False,
        **kwargs
    )
