"""
Main application module for Excel-Cleaner backend.
This module serves as the entry point for the backend service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import router as api_router

# Initialize FastAPI application
app = FastAPI(
    title="Excel-Cleaner Backend",
    description="Backend service for Excel file processing and analysis",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message and API information."""
    return {
        "message": "Welcome to Excel-Cleaner Backend Service",
        "version": app.version,
        "status": "running",
        "docs": {
            "swagger": "/api/v1/docs",
            "redoc": "/api/v1/redoc",
            "openapi_schema": "/api/v1/openapi.json"
        }
    }
