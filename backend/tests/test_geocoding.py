"""
Unit Tests for Geocoding and Cache
"""
import os
import tempfile
from app.services.geocoding.cache import GeocodeCache
from app.services.geocoding.base import GeocodeResult


async def test_geocode_cache_set_and_get():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_cache_file = tf.name

    try:
        cache = GeocodeCache(cache_file_path=temp_cache_file)
        # Test miss
        cached = await cache.get("Unknown Address")
        assert cached is None

        # Test set and hit
        await cache.set("Bandra Kurla Complex, Mumbai", 19.0657, 72.8687, "BKC, Mumbai")
        cached = await cache.get("Bandra Kurla Complex, Mumbai")
        assert cached is not None
        lat, lon, name = cached
        assert lat == 19.0657
        assert lon == 72.8687

        # Test case-insensitivity and whitespace normalization
        cached_norm = await cache.get("   bandra  kurla   complex, MUMBAI  ")
        assert cached_norm is not None
        assert cached_norm[0] == 19.0657
    finally:
        if os.path.exists(temp_cache_file):
            os.remove(temp_cache_file)
