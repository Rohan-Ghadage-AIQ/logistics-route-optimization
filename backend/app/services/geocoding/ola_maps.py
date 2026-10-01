"""
Ola Maps Geocoder Implementation (Krutrim Geocoding API)
"""
import asyncio
from typing import List, Optional
import httpx
from app.services.geocoding.base import BaseGeocoder, GeocodeResult
from app.services.geocoding.cache import GeocodeCache
from app.utils.logger import logger


class OlaMapsGeocoder(BaseGeocoder):
    """Ola Maps (Krutrim) Geocoding Client with parallel batching."""

    def __init__(
        self,
        api_key: Optional[str],
        cache: GeocodeCache,
        base_url: str = "https://api.olamaps.io/places/v1/geocode",
        max_concurrent: int = 5
    ):
        self.api_key = api_key
        self.cache = cache
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def geocode(self, address: str) -> GeocodeResult:
        if not address or not address.strip():
            return GeocodeResult(raw_address=address, success=False, error="Empty address string")

        # 1. Check cache first
        cached = await self.cache.get(address)
        if cached:
            lat, lon, res_name = cached
            return GeocodeResult(
                raw_address=address,
                resolved_address=res_name,
                latitude=lat,
                longitude=lon,
                success=True,
                is_cached=True
            )

        if not self.api_key:
            return GeocodeResult(raw_address=address, success=False, error="Ola Maps API key not configured")

        params = {
            "address": address,
            "api_key": self.api_key
        }
        headers = {
            "Origin": "http://localhost"
        }

        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(self.base_url, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        geocoding_results = data.get("geocodingResults", [])
                        if geocoding_results:
                            top = geocoding_results[0]
                            geometry = top.get("geometry", {}).get("location", {})
                            lat = float(geometry.get("lat", 0.0))
                            lon = float(geometry.get("lng", 0.0))
                            formatted_addr = top.get("formatted_address", address)

                            if lat != 0.0 and lon != 0.0:
                                await self.cache.set(address, lat, lon, formatted_addr)
                                return GeocodeResult(
                                    raw_address=address,
                                    resolved_address=formatted_addr,
                                    latitude=lat,
                                    longitude=lon,
                                    success=True,
                                    is_cached=False
                                )

                        return GeocodeResult(raw_address=address, success=False, error="No coordinates found in Ola Maps")
                    else:
                        return GeocodeResult(raw_address=address, success=False, error=f"Ola Maps returned {resp.status_code}")
            except Exception as e:
                logger.error(f"Ola Maps error for '{address}': {e}")
                return GeocodeResult(raw_address=address, success=False, error=str(e))

    async def geocode_batch(self, addresses: List[str]) -> List[GeocodeResult]:
        tasks = [self.geocode(addr) for addr in addresses]
        return await asyncio.gather(*tasks)
