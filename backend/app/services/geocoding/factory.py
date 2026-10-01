"""
Geocoding Service Factory and Multi-Tier Orchestrator
Provides single point of entry with caching and transparent fallback.
"""
from typing import List
from app.config import settings
from app.services.geocoding.base import BaseGeocoder, GeocodeResult
from app.services.geocoding.cache import GeocodeCache
from app.services.geocoding.nominatim import NominatimGeocoder
from app.services.geocoding.ola_maps import OlaMapsGeocoder
from app.utils.logger import logger


class GeocodingService(BaseGeocoder):
    """
    Unified Geocoding Service with multi-tier fallback:
    1. Geocode Cache (0ms)
    2. Primary Provider (Ola Maps or Nominatim)
    3. Secondary Fallback Provider (Nominatim)
    """

    def __init__(self):
        self.cache = GeocodeCache(cache_file_path=settings.GEOCODING_CACHE_FILE)
        self.nominatim = NominatimGeocoder(
            cache=self.cache,
            rate_limit_delay=settings.GEOCODING_RATE_LIMIT_DELAY_SECONDS
        )
        self.ola = OlaMapsGeocoder(
            api_key=settings.GEOCODING_API_KEY,
            cache=self.cache,
            max_concurrent=settings.GEOCODING_MAX_CONCURRENT_REQUESTS
        )
        self.provider_name = settings.GEOCODING_PROVIDER.lower()

    async def geocode(self, address: str) -> GeocodeResult:
        """Geocodes with caching and fallback."""
        # 1. Primary provider
        if self.provider_name == "ola" and settings.GEOCODING_API_KEY:
            result = await self.ola.geocode(address)
            if result.success:
                return result
            logger.warning(f"Ola Maps geocoding failed for '{address}'. Falling back to Nominatim.")

        # 2. Nominatim fallback (or primary if chosen)
        return await self.nominatim.geocode(address)

    async def geocode_batch(self, addresses: List[str]) -> List[GeocodeResult]:
        """Geocodes batch with caching and fallback."""
        results: List[GeocodeResult] = []
        for addr in addresses:
            res = await self.geocode(addr)
            results.append(res)
        return results


geocoding_service = GeocodingService()
