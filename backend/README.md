# Excel-Cleaner Backend

Backend service for Excel-Cleaner, a powerful tool for processing, analyzing, and visualizing Excel/CSV data.

## Features

- **Data Processing**: Load, clean, and transform Excel/CSV data
- **Analysis**: Perform calculations, aggregations, and statistical analysis
- **Visualization**: Generate various charts and plots
- **Report Generation**: Create reports in Excel and PDF formats
- **RESTful API**: Built with FastAPI for easy integration

## Project Structure

```
backend/
├── app/                      # Main application package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── core/                # Core business logic
│   │   ├── __init__.py
│   │   ├── data_processor.py  # Data processing logic
│   │   ├── excel_handler.py   # Excel file operations
│   │   └── report_generator.py # Report generation
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── data_cleaning.py   # Data cleaning operations
│   │   ├── calculations.py    # Data calculations
│   │   └── visualization.py   # Data visualization
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── file_handlers.py   # File I/O operations
│       └── validators.py      # Data validation
├── tests/                   # Unit and integration tests
│   ├── __init__.py
│   ├── test_data_cleaning.py
│   └── test_calculations.py
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd excel-cleaner/backend
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the FastAPI development server:

   ```bash
   uvicorn app.main:app --reload
   ```

2. The API will be available at `http://127.0.0.1:8000`

3. Access the interactive API documentation at:
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

- `GET /`: Health check and API information
- `POST /api/v1/upload`: Upload and process Excel/CSV files
- `POST /api/v1/clean`: Clean and preprocess data
- `POST /api/v1/analyze`: Perform data analysis
- `POST /api/v1/visualize`: Generate visualizations
- `POST /api/v1/export`: Export processed data

## Development

### Code Style

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.

### Testing

Run tests using pytest:

```bash
pytest
```

### Linting

Check code style with flake8:

```bash
flake8 .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
