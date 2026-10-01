"""
Abstract Base Geocoding Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel


class GeocodeResult(BaseModel):
    raw_address: str
    resolved_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    success: bool
    error: Optional[str] = None
    is_cached: bool = False


class BaseGeocoder(ABC):
    """Abstract interface for all geocoding service implementations."""

    @abstractmethod
    async def geocode(self, address: str) -> GeocodeResult:
        """Geocode a single raw address string."""
        pass

    @abstractmethod
    async def geocode_batch(self, addresses: List[str]) -> List[GeocodeResult]:
        """Geocode a batch of raw address strings."""
        pass
