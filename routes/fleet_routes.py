# routes/fleet_routes.py
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from auth import fleet_required, login_required
from models import db, Vehicle, Trip, Battery
from services import analytics

bp = Blueprint("fleet", __name__, url_prefix="/api/fleet")

@bp.get("/vehicles")
@fleet_required
def list_vehicles():
    user = g.current_user
    q = Vehicle.query
    if user.role == "fleet":
        q = q.filter_by(company_id=user.company_id)
    return jsonify({"ok": True, "data": [v.to_dict() for v in q.all()]})

@bp.post("/vehicles")
@fleet_required
def add_vehicle():
    data = request.get_json() or {}
    user = g.current_user
    v = Vehicle(
        plate=data["plate"],
        model=data.get("model", "MAPNA E-Motor 125"),
        owner_id=data.get("owner_id") or user.id,
        company_id=user.company_id if user.role == "fleet" else data.get("company_id"),
        battery_id=data.get("battery_id"),
        odometer_km=float(data.get("odometer_km", 0.0)),
        last_service_km=float(data.get("last_service_km", 0.0)),
        service_interval_km=float(data.get("service_interval_km", 5000.0)),
        in_pilot=bool(data.get("in_pilot", True)),
    )
    db.session.add(v)
    db.session.commit()
    return jsonify({"ok": True, "data": v.to_dict()}), 201

@bp.patch("/vehicles/<int:vid>")
@fleet_required
def update_vehicle(vid):
    v = Vehicle.query.get_or_404(vid)
    data = request.get_json() or {}
    for f in ["status", "odometer_km", "last_service_km", "battery_id", "in_pilot"]:
        if f in data:
            setattr(v, f, data[f])
    db.session.commit()
    return jsonify({"ok": True, "data": v.to_dict()})

@bp.get("/trips")
@fleet_required
def list_trips():
    user = g.current_user
    q = Trip.query
    if user.role == "fleet" and user.company_id:
        q = q.join(Vehicle, Vehicle.id == Trip.vehicle_id).filter(Vehicle.company_id == user.company_id)
    trips = q.order_by(Trip.started_at.desc()).limit(100).all()
    return jsonify({"ok": True, "data": [t.to_dict() for t in trips]})

@bp.post("/trips")
@login_required
def add_trip():
    """ایجاد سفر جدید (معمولاً توسط موتورسوار یا خودرو)"""
    data = request.get_json() or {}
    t = Trip(
        rider_id=data.get("rider_id") or g.current_user.id,
        vehicle_id=data["vehicle_id"],
        start_lat=float(data["start_lat"]),
        start_lng=float(data["start_lng"]),
        end_lat=data.get("end_lat"),
        end_lng=data.get("end_lng"),
        distance_km=float(data.get("distance_km", 0.0)),
        energy_kwh=float(data.get("energy_kwh", 0.0)),
        co2_saved_kg=float(data.get("co2_saved_kg", 0.0)),
        cost_toman=float(data.get("cost_toman", 0.0)),
        weather=data.get("weather", "clear"),
        ended_at=datetime.utcnow() if data.get("end_lat") else None,
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"ok": True, "data": t.to_dict()}), 201