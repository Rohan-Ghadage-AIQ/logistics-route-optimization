"""
Health Check & Service Status API Router
"""
from fastapi import APIRouter
from app.config import settings
from app.services.valhalla.client import valhalla_client

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """System health check and dependency connectivity status."""
    valhalla_healthy = await valhalla_client.is_healthy()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "dependencies": {
            "valhalla_routing_engine": {
                "status": "connected" if valhalla_healthy else "disconnected_or_fallback",
                "base_url": settings.VALHALLA_BASE_URL,
                "reachable": valhalla_healthy
            },
            "geocoding_provider": {
                "provider": settings.GEOCODING_PROVIDER,
                "cache_file": settings.GEOCODING_CACHE_FILE
            },
            "database": {
                "url": settings.DATABASE_URL.split("///")[-1]  # Hide credentials if any
            }
        }
    }
