"""
API routes package for Excel-Cleaner.
Contains route modules for different API endpoints.
"""
from fastapi import APIRouter

# Create a router for all routes
router = APIRouter()

from . import file_routes
from . import pivot_routes
from . import chart_routes
from . import export_routes

router.include_router(file_routes.router, tags=["files"])
router.include_router(pivot_routes.router, tags=["pivot"])
router.include_router(chart_routes.router, tags=["charts"])
router.include_router(export_routes.router, tags=["export"])
