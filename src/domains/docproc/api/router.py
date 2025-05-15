"""
Main router for the users domain.
"""

from fastapi import APIRouter

from src.domains.docproc.api.v1.test import router as test_router

router = APIRouter(prefix="/docproc", tags=["docproc"])
router.include_router(test_router)
