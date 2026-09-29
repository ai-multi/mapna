"""
MAPNA SwapFleet AI - Configuration
"""
import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "swapfleet-dev-secret-key-change-in-prod")
    JSON_SORT_KEYS = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///swapfleet.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "swapfleet-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ["headers"]

    # Bcrypt
    BCRYPT_LOG_ROUNDS = 12

    # AI / LLM
    LLM_MODE = os.getenv("LLM_MODE", "mock")  # "mock" | "avalai"
    AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")
    AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
    AVALAI_MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")

    # Business constants
    DEFAULT_BATTERY_CAPACITY_KWH = 2.5
    CO2_PER_KWH_GRID_KG = 0.55        # ضریب آلایندگی شبکه برق ایران
    MOTORCYCLE_FUEL_L_PER_100KM = 2.5  # مصرف سوخت بنزینی معادل
    CO2_PER_LITER_GASOLINE_KG = 2.31
    KWH_PER_KM_EV = 0.05               # مصرف برق موتور برقی

    # Pricing
    BASE_SWAP_PRICE = 35000  # تومان
    PRICE_DEMAND_LOW = 0.9
    PRICE_DEMAND_NORMAL = 1.0
    PRICE_DEMAND_HIGH = 1.25
    PRICE_DEMAND_PEAK = 1.5

    # Tehran default center
    TEHRAN_CENTER = {"lat": 35.6892, "lng": 51.3890}