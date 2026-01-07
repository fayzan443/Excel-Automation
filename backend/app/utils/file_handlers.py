"""
File handling utilities for Excel-Cleaner.
Handles file operations like reading, writing, and validation.
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
import mimetypes

class FileHandler:
    """Handles file operations for the application."""
    
    # Supported file extensions and their corresponding pandas read functions
    READ_FUNCTIONS = {
        '.csv': pd.read_csv,
        '.xlsx': pd.read_excel,
        '.xls': pd.read_excel,
        '.json': pd.read_json,
        '.parquet': pd.read_parquet,
        '.feather': pd.read_feather,
        '.h5': pd.read_hdf,
        '.hdf5': pd.read_hdf,
    }
    
    # Supported file extensions for writing
    WRITE_FUNCTIONS = {
        '.csv': 'to_csv',
        '.xlsx': 'to_excel',
        '.xls': 'to_excel',
        '.json': 'to_json',
        '.parquet': 'to_parquet',
        '.feather': 'to_feather',
        '.h5': 'to_hdf',
        '.hdf5': 'to_hdf',
    }
    
    @classmethod
    def get_file_extension(cls, file_path: str) -> str:
        """
        Get the file extension in lowercase.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension with leading dot (e.g., '.csv')
        """
        return os.path.splitext(file_path)[1].lower()
    
    @classmethod
    def is_supported_file(cls, file_path: str, mode: str = 'read') -> bool:
        """
        Check if the file format is supported.
        
        Args:
            file_path: Path to the file
            mode: 'read' or 'write'
            
        Returns:
            True if the file format is supported, False otherwise
        """
        ext = cls.get_file_extension(file_path)
        if mode == 'read':
            return ext in cls.READ_FUNCTIONS
        return ext in cls.WRITE_FUNCTIONS
    
    @classmethod
    def read_file(
        cls,
        file_path: str,
        **kwargs
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Read a file into a pandas DataFrame or a dictionary of DataFrames.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments to pass to the pandas read function
            
        Returns:
            DataFrame or dictionary of DataFrames
            
        Raises:
            ValueError: If the file format is not supported
        """
        ext = cls.get_file_extension(file_path)
        if ext not in cls.READ_FUNCTIONS:
            raise ValueError(f"Unsupported file format: {ext}")
        
        read_func = cls.READ_FUNCTIONS[ext]
        
        # Handle Excel files differently to support multiple sheets
        if ext in ['.xlsx', '.xls']:
            xls = pd.ExcelFile(file_path)
            return {sheet: pd.read_excel(xls, sheet_name=sheet, **kwargs) 
                   for sheet in xls.sheet_names}
        
        # For other file types, use the appropriate read function
        return read_func(file_path, **kwargs)
    
    @classmethod
    def write_file(
        cls,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        file_path: str,
        **kwargs
    ) -> None:
        """
        Write data to a file.
        
        Args:
            data: DataFrame or dictionary of DataFrames to write
            file_path: Path where to save the file
            **kwargs: Additional arguments to pass to the pandas write function
            
        Raises:
            ValueError: If the file format is not supported
        """
        ext = cls.get_file_extension(file_path)
        if ext not in cls.WRITE_FUNCTIONS:
            raise ValueError(f"Unsupported file format for writing: {ext}")
        
        write_method = cls.WRITE_FUNCTIONS[ext]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Handle Excel files differently to support multiple sheets
        if ext in ['.xlsx', '.xls']:
            if isinstance(data, dict):
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for sheet_name, df in data.items():
                        df.to_excel(writer, sheet_name=sheet_name, **kwargs)
            else:
                data.to_excel(file_path, **kwargs)
        else:
            # For other file types
            if isinstance(data, dict) and len(data) == 1:
                # If single sheet, write the only DataFrame
                getattr(next(iter(data.values())), write_method)(file_path, **kwargs)
            elif isinstance(data, pd.DataFrame):
                getattr(data, write_method)(file_path, **kwargs)
            else:
                raise ValueError("Cannot write multiple DataFrames to a single non-Excel file")
