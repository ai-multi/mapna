# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "swapfleet-secret-key-2024-mapoora")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "swapfleet-jwt-secret-2024-mapoora")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///swapfleet.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AVALAI config (mock if not set)
    AVALAI_API_KEY = os.environ.get("AVALAI_API_KEY", "")
    AVALAI_BASE_URL = os.environ.get(
        "AVALAI_BASE_URL", "https://api.avalai.ir/v1"
    )
    AVALAI_MODEL = os.environ.get("AVALAI_MODEL", "gpt-4o-mini")

    # Business constants
    BASE_PRICE_PER_KWH = 8500  # تومان
    CO2_PER_KWH_GRID = 0.7    # کیلوگرم
    CO2_PER_KWH_SAVED = 0.55  # کیلوگرم (نسبت به بنزین)
    DEFAULT_BATTERY_CAPACITY_KWH = 3.0