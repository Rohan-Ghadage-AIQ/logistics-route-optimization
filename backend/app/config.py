import os
from typing import List, Optional
from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    class _BaseSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
except ImportError:
    from pydantic import BaseModel
    class _BaseSettings(BaseModel):
        pass


class Settings(_BaseSettings):

    # Application Info
    APP_NAME: str = "Logistics Route Optimization System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:80", "*"]

    # Database Configuration (Async SQLite default, PostgreSQL compatible)
    DATABASE_URL: str = "sqlite+aiosqlite:///./logistics_optimization.db"

    # Valhalla Routing Engine Configuration
    VALHALLA_BASE_URL: str = "http://localhost:8002"
    VALHALLA_TIMEOUT_SECONDS: float = 30.0
    VALHALLA_COSTING: str = "auto"  # 'auto', 'truck', 'motorcycle'

    # Geocoding Configuration
    GEOCODING_PROVIDER: str = "nominatim"  # 'nominatim', 'ola', 'mock'
    GEOCODING_API_KEY: Optional[str] = None
    GEOCODING_CACHE_FILE: str = "./geocode_cache.json"
    GEOCODING_RATE_LIMIT_DELAY_SECONDS: float = 0.2
    GEOCODING_MAX_CONCURRENT_REQUESTS: int = 5

    # Default Warehouse / Depot Configuration
    DEPOT_NAME: str = "Central Fulfillment Depot"
    DEPOT_LATITUDE: float = 19.0550
    DEPOT_LONGITUDE: float = 72.8750
    DEPOT_LOADING_DURATION_MINUTES: int = 10

    # Optimization Engine Parameters
    OPTIMIZATION_SOLVER_TIME_LIMIT_SECONDS: int = 10
    OPTIMIZATION_WAITING_SLACK_MINUTES: int = 20  # Max waiting buffer allowed between stops (prevents long waiting)
    OVERTIME_BUFFER_MINUTES: int = 30
    FIXED_VEHICLE_DISPATCH_COST: int = 300
    DROP_PENALTY_MULTIPLIER: int = 1_000_000_000
    TIME_WINDOW_PENALTY_PER_MINUTE: int = 100_000
    OVERCAPACITY_PENALTY_PER_KG: int = 1_000_000
    SHIFT_OVERTIME_PENALTY_PER_MINUTE: int = 50_000
    WAITING_SPAN_PENALTY_WEIGHT: int = 500  # Penalize vehicle idle waiting duration in solver objective


settings = Settings()
