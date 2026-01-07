"""
API package for Excel-Cleaner backend.
Contains all API routes and endpoints.
"""
from fastapi import APIRouter

# Create a router for all API endpoints
router = APIRouter(prefix="/api/v1")

from .routes import router as routes_router

router.include_router(routes_router)
