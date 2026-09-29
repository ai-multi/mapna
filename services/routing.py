# services/routing.py
import math
from datetime import datetime
from models import SwapStation, Battery

# شعاع تقریبی زمین (کیلومتر)
EARTH_RADIUS_KM = 6371.0

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """فاصله کروی بین دو نقطه بر حسب کیلومتر"""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return round(EARTH_RADIUS_KM * c, 3)

def weather_penalty(weather: str) -> float:
    """ضریب تشدید مصرف باتری بر اساس آب و هوا"""
    weather = (weather or "").lower()
    if "rain" in weather or "snow" in weather:
        return 1.20
    if "wind" in weather:
        return 1.10
    if "cold" in weather or "سرد" in weather:
        return 1.15
    if "hot" in weather or "گرم" in weather:
        return 1.08
    return 1.0

def energy_for_trip_km(distance_km: float, weather: str = "clear") -> float:
    """برآورد انرژی لازم برای پیمایش مسافت (kWh).
    فرض: موتور 125cc برقی ≈ 30 Wh/km
    """
    base_kwh_per_km = 0.030
    return round(distance_km * base_kwh_per_km * weather_penalty(weather), 3)

def reachable_radius_km(soc_percent: float, weather: str = "clear", capacity_kwh: float = 3.0) -> float:
    """شعاع قابل پیمایش با درصد باتری فعلی (کیلومتر)"""
    usable_kwh = (soc_percent / 100.0) * capacity_kwh
    base_kwh_per_km = 0.030
    return round((usable_kwh / base_kwh_per_km) / weather_penalty(weather), 2)

def score_station(
    station: SwapStation,
    distance_km: float,
    soc_percent: float,
    user_pref: str = "balanced",
    weather: str = "clear",
    batteries_ready: int = 0,
) -> dict:
    """
    امتیازدهی ایستگاه.
    user_pref: 'fastest' (کمترین فاصله), 'cheapest' (کمترین اشغال),
                'balanced' (ترکیبی), 'available' (بالاترین ظرفیت خالی).
    """
    if station.available_slots <= 0 or not station.is_active:
        return None

    # عوامل پایه
    dist_score = max(0.0, 1.0 - distance_km / 20.0)  # فاصله کمتر بهتر
    occ_score = 1.0 - station.occupancy_ratio()        # ظرفیت بیشتر بهتر
    battery_score = min(1.0, batteries_ready / 5.0)
    reach_score = 1.0 if distance_km <= reachable_radius_km(soc_percent, weather) else 0.4

    if user_pref == "fastest":
        weight = (0.7, 0.1, 0.1, 0.1)
    elif user_pref == "cheapest":
        weight = (0.2, 0.5, 0.1, 0.2)
    elif user_pref == "available":
        weight = (0.2, 0.4, 0.3, 0.1)
    else:  # balanced
        weight = (0.35, 0.25, 0.2, 0.2)

    final_score = (
        dist_score * weight[0]
        + occ_score * weight[1]
        + battery_score * weight[2]
        + reach_score * weight[3]
    )

    return {
        "station_id": station.id,
        "station_name": station.name,
        "lat": station.lat,
        "lng": station.lng,
        "distance_km": distance_km,
        "available_slots": station.available_slots,
        "batteries_ready": batteries_ready,
        "score": round(final_score, 3),
        "reachable": reach_score == 1.0,
    }

def plan_route(
    user_lat: float,
    user_lng: float,
    dest_lat: float = None,
    dest_lng: float = None,
    soc_percent: float = 50.0,
    weather: str = "clear",
    preference: str = "balanced",
) -> dict:
    """پیشنهاد بهترین ایستگاه سواپ در مسیر"""
    stations = SwapStation.query.filter_by(is_active=True).all()

    # شعاع قابل پیمایش با باتری فعلی
    radius = reachable_radius_km(soc_percent, weather)

    # فاصله تا مقصد (اگر باشد)
    dest_distance = None
    if dest_lat is not None and dest_lng is not None:
        dest_distance = haversine_km(user_lat, user_lng, dest_lat, dest_lng)

    candidates = []
    for st in stations:
        d = haversine_km(user_lat, user_lng, st.lat, st.lng)
        ready = Battery.query.filter_by(
            current_station_id=st.id, status="ready", soc__gte=80  # noqa: E711
        ).count() if hasattr(Battery, "soc__gte") else Battery.query.filter(
            Battery.current_station_id == st.id,
            Battery.status == "ready",
            Battery.soc >= 80
        ).count()

        info = score_station(st, d, soc_percent, preference, weather, ready)
        if info:
            # فقط ایستگاه‌هایی که در مسیر تقریبی قرار دارند (شعاع 1.5x)
            if dest_distance is None or d <= radius * 1.5:
                candidates.append(info)

    candidates.sort(key=lambda x: x["score"], reverse=True)

    eta_minutes = None
    if dest_distance is not None:
        eta_minutes = round((dest_distance / 35.0) * 60, 1)  # 35 km/h میانگین

    return {
        "origin": {"lat": user_lat, "lng": user_lng},
        "destination": (
            {"lat": dest_lat, "lng": dest_lng} if dest_lat is not None else None
        ),
        "reachable_radius_km": radius,
        "weather": weather,
        "preference": preference,
        "dest_distance_km": dest_distance,
        "eta_minutes": eta_minutes,
        "candidates": candidates[:8],
        "recommended": candidates[0] if candidates else None,
        "timestamp": datetime.utcnow().isoformat(),
    }