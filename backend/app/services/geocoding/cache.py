"""
Thread-safe & Async-safe JSON Geocode Cache
Supports direct address keys and MD5 hash keys.
"""
import os
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, Tuple
from app.utils.logger import logger


class GeocodeCache:
    """Manages persistent caching of address geocoding results."""

    def __init__(self, cache_file_path: str = "./geocode_cache.json"):
        self.cache_file_path = cache_file_path
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _normalize_key(self, address: str) -> str:
        """Normalize address text for consistent cache lookup."""
        return " ".join(address.strip().lower().split())

    def _hash_key(self, address: str) -> str:
        """Generate MD5 hash key matching legacy cache format."""
        return hashlib.md5(self._normalize_key(address).encode("utf-8")).hexdigest()

    def _load(self) -> None:
        """Loads cache file from disk."""
        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} cached geocode entries from {self.cache_file_path}")
            except Exception as e:
                logger.warning(f"Failed to read geocode cache from {self.cache_file_path}: {e}")
                self._cache = {}
        else:
            self._cache = {}

    async def get(self, address: str) -> Optional[Tuple[float, float, str]]:
        """
        Retrieves cached coordinates and resolved name.
        Checks both normalized address key and MD5 hash key.
        """
        async with self._lock:
            norm_key = self._normalize_key(address)
            hash_key = self._hash_key(address)

            entry = self._cache.get(norm_key) or self._cache.get(hash_key)
            if entry:
                lat = entry.get("lat") or entry.get("latitude")
                lon = entry.get("lon") or entry.get("longitude")
                name = entry.get("resolved_address") or entry.get("formatted_address", address)
                if lat is not None and lon is not None:
                    return float(lat), float(lon), str(name)
            return None

    async def set(self, address: str, lat: float, lon: float, resolved_address: Optional[str] = None) -> None:
        """Saves a newly geocoded address to in-memory cache and persists to disk."""
        async with self._lock:
            norm_key = self._normalize_key(address)
            self._cache[norm_key] = {
                "lat": float(lat),
                "lon": float(lon),
                "resolved_address": resolved_address or address
            }
            self._persist()

    def _persist(self) -> None:
        """Writes current cache to disk file."""
        try:
            with open(self.cache_file_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write geocode cache to disk: {e}")
