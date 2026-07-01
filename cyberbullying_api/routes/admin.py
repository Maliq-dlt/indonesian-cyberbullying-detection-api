"""Admin router aggregator.

This module re-exports routers from the split sub-modules for backward
compatibility. All route logic has been moved to:
- routes.auth       — JWT login (public_router)
- routes.scraper    — TikTok & X scraping
- routes.hitl       — Human-in-the-loop data management
- routes.training   — Model training, reload, log streaming, history
- routes.settings   — Cookies, webhook config, recalibration
"""

from fastapi import APIRouter
from routes.auth import public_router as public_router
from routes.hitl import router as hitl_router
from routes.scraper import router as scraper_router
from routes.settings import router as settings_router
from routes.training import router as training_router

# Compose a single admin_router from all sub-modules
router = APIRouter()
router.include_router(scraper_router)
router.include_router(hitl_router)
router.include_router(training_router)
router.include_router(settings_router)
