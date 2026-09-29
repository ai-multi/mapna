# services/analytics.py
from datetime import datetime, timedelta
from sqlalchemy import func
from models import (
    db, SwapEvent, Trip, Vehicle, Battery, User,
    MaintenanceTicket, SwapStation
)
from config import Config

def co2_saved_kwh(energy_kwh: float) -> float:
    """CO2 صرفه‌جویی شده برای مقدار انرژی"""
    return round(energy_kwh * Config.CO2_PER_KWH_SAVED, 3)

def overview() -> dict:
    """آمار کلی برای داشبورد ادمین"""
    total_stations = SwapStation.query.count()
    active_stations = SwapStation.query.filter_by(is_active=True).count()
    total_slots = db.session.query(func.sum(SwapStation.capacity_slots)).scalar() or 0
    free_slots = db.session.query(func.sum(SwapStation.available_slots)).scalar() or 0
    total_batteries = Battery.query.count()
    ready_batteries = Battery.query.filter_by(status="ready").count()
    avg_soc = db.session.query(func.avg(Battery.soc)).filter(Battery.status.in_(["ready", "charging"])).scalar() or 0
    total_vehicles = Vehicle.query.count()
    in_service = Vehicle.query.filter_by(status="in_service").count()
    pilot_vehicles = Vehicle.query.filter_by(in_pilot=True).count()
    total_users = User.query.count()

    # uptime/downtime تقریبی بر اساس ایستگاه‌ها
    active_ratio = (active_stations / total_stations) if total_stations else 0

    # CO2 کل صرفه‌جویی شده
    total_energy = db.session.query(func.sum(SwapEvent.energy_kwh)).scalar() or 0
    total_co2 = co2_saved_kwh(total_energy)

    return {
        "stations": {
            "total": total_stations,
            "active": active_stations,
            "total_slots": int(total_slots),
            "free_slots": int(free_slots),
        },
        "batteries": {
            "total": total_batteries,
            "ready": ready_batteries,
            "avg_soc": round(avg_soc, 1),
        },
        "vehicles": {
            "total": total_vehicles,
            "in_service": in_service,
            "pilot": pilot_vehicles,
            "uptime_ratio": round(active_ratio, 3),
            "downtime_ratio": round(1 - active_ratio, 3),
        },
        "users": {"total": total_users},
        "sustainability": {
            "total_energy_kwh": round(total_energy, 2),
            "total_co2_saved_kg": round(total_co2, 2),
            "co2_saved_trees_equivalent": round(total_co2 / 21, 1),
        },
    }

def station_performance() -> list:
    """عملکرد هر ایستگاه"""
    stations = SwapStation.query.all()
    out = []
    for s in stations:
        events = SwapEvent.query.filter_by(station_id=s.id).all()
        total_swaps = len(events)
        revenue = sum(e.price_toman for e in events)
        energy = sum(e.energy_kwh for e in events)
        co2 = co2_saved_kwh(energy)
        out.append({
            "station_id": s.id,
            "station_name": s.name,
            "available_slots": s.available_slots,
            "capacity_slots": s.capacity_slots,
            "occupancy_ratio": s.occupancy_ratio(),
            "total_swaps": total_swaps,
            "revenue_toman": int(revenue),
            "energy_kwh": round(energy, 2),
            "co2_saved_kg": round(co2, 2),
        })
    out.sort(key=lambda x: x["total_swaps"], reverse=True)
    return out

def rider_history(rider_id: int, days: int = 30) -> dict:
    """تاریخچه و آمار یک موتورسوار"""
    since = datetime.utcnow() - timedelta(days=days)
    trips = Trip.query.filter(Trip.rider_id == rider_id, Trip.started_at >= since).all()
    swaps = SwapEvent.query.filter(SwapEvent.user_id == rider_id, SwapEvent.created_at >= since).all()

    total_distance = sum(t.distance_km or 0 for t in trips)
    total_energy = sum(t.energy_kwh or 0 for t in trips) + sum(s.energy_kwh or 0 for s in swaps)
    total_cost = sum(t.cost_toman or 0 for t in trips) + sum(s.price_toman or 0 for s in swaps)
    total_co2 = co2_saved_kwh(total_energy)

    return {
        "rider_id": rider_id,
        "days": days,
        "trip_count": len(trips),
        "swap_count": len(swaps),
        "total_distance_km": round(total_distance, 2),
        "total_energy_kwh": round(total_energy, 2),
        "total_cost_toman": int(total_cost),
        "co2_saved_kg": round(total_co2, 2),
        "trips": [t.to_dict() for t in trips[-10:]],
        "swaps": [s.to_dict() for s in swaps[-10:]],
    }

def fleet_health(company_id: int = None) -> dict:
    """سلامت ناوگان"""
    q = Vehicle.query
    if company_id is not None:
        q = q.filter_by(company_id=company_id)
    vehicles = q.all()
    vehicles_out = [v.to_dict() for v in vehicles]

    statuses = {}
    for v in vehicles:
        statuses[v.status] = statuses.get(v.status, 0) + 1

    service_due = sum(1 for v in vehicles if v.service_due_soon())

    # میانگین soc باتری‌های ناوگان
    batteries = []
    for v in vehicles:
        if v.battery_id:
            b = Battery.query.get(v.battery_id)
            if b:
                batteries.append(b)
    avg_soc = sum(b.soc for b in batteries) / len(batteries) if batteries else 0
    avg_soh = sum(b.soh for b in batteries) / len(batteries) if batteries else 0

    return {
        "vehicle_count": len(vehicles),
        "status_breakdown": statuses,
        "service_due_count": service_due,
        "avg_battery_soc": round(avg_soc, 1),
        "avg_battery_soh": round(avg_soh, 1),
        "vehicles": vehicles_out,
    }

def recent_alerts(limit: int = 10) -> list:
    """هشدارها و خرابی‌های اخیر"""
    tickets = (
        MaintenanceTicket.query
        .order_by(MaintenanceTicket.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for t in tickets:
        info = t.to_dict()
        if t.battery:
            info["battery_serial"] = t.battery.serial
            info["battery_soh"] = t.battery.soh
        out.append(info)
    return out

def recent_swaps(limit: int = 20) -> list:
    events = SwapEvent.query.order_by(SwapEvent.created_at.desc()).limit(limit).all()
    return [e.to_dict() for e in events]