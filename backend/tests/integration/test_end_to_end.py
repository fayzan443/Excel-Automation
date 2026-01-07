"""
Integration tests for the entire Excel-Cleaner pipeline.
"""
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.services.data_cleaning import DataCleaningService
from app.services.calculations import CalculationService
from app.services.pivot_service import PivotService, PivotConfig

class TestEndToEnd:
    """End-to-end test cases for the Excel-Cleaner pipeline."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        with TestClient(app) as client:
            yield client
    
    def test_full_pipeline(self, sample_data):
        """Test the full data processing pipeline."""
        # 1. Data Cleaning
        df = sample_data['sales'].copy()
        
        # Add some test data issues
        df_with_issues = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # Duplicate row
        df_with_issues.loc[0, 'quantity'] = None  # Missing value
        
        # Clean the data
        cleaned_df = DataCleaningService.remove_duplicates(df_with_issues)
        cleaned_df = DataCleaningService.handle_missing_values(
            cleaned_df, 
            strategy='mean', 
            columns=['quantity']
        )
        
        # Verify cleaning
        assert len(cleaned_df) == len(df)
        assert not cleaned_df['quantity'].isna().any()
        
        # 2. Calculations
        calculations = [
            {"column": "total", "formula": "quantity * price * (1 - discount)"},
            {"column": "is_high_value", "formula": "total > 2000"}
        ]
        calculated_df = CalculationService.calculate_columns(cleaned_df, calculations)
        
        # Verify calculations
        expected_total = cleaned_df['quantity'] * cleaned_df['price'] * (1 - cleaned_df['discount'])
        pd.testing.assert_series_equal(
            calculated_df['total'].round(2), 
            expected_total.round(2),
            check_names=False
        )
        
        # 3. Pivot Table
        pivot_config = PivotConfig(
            index=['category'],
            columns=['product'],
            values=['total'],
            aggfunc='sum',
            margins=True
        )
        pivot_result = PivotService.create_pivot(calculated_df, pivot_config)
        
        # Verify pivot
        assert pivot_result['success'] is True
        assert 'data' in pivot_result
        assert 'total' in str(pivot_result['data'])
        
        # 4. API Endpoint Test
        with TestClient(app) as client:
            # Upload test data
            test_data = {
                'file': ('test.xlsx', sample_data['sales'].to_csv(index=False).encode())
            }
            response = client.post("/api/upload", files=test_data)
            assert response.status_code == 200
            file_id = response.json()['data']['file_id']
            
            # Test pivot endpoint
            pivot_request = {
                "index": ["category"],
                "columns": ["product"],
                "values": ["total"],
                "aggfunc": "sum"
            }
            response = client.post(f"/api/pivot/{file_id}", json=[pivot_request])
            assert response.status_code == 200
            assert response.json()['success'] is True
            
            # Test chart endpoint
            chart_config = {
                "chart_type": "bar",
                "x": "category",
                "y": "total",
                "title": "Test Chart"
            }
            response = client.post(f"/api/chart/{file_id}", json=[chart_config])
            assert response.status_code == 200
            assert 'image_data' in response.json()['data']
            
            # Test export endpoint
            response = client.get(f"/api/export/{file_id}?format=excel")
            assert response.status_code == 200
            assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers['content-type']
