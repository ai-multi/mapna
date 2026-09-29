# routes/station_routes.py
from flask import Blueprint, request, jsonify, g
from auth import station_required
from models import db, Battery, SwapStation, StationSlot

bp = Blueprint("station", __name__, url_prefix="/api/station")

@bp.get("/my")
@station_required
def my_station():
    """ایستگاه‌های تحت مدیریت کاربر فعلی"""
    user = g.current_user
    stations = SwapStation.query.filter_by(manager_id=user.id).all()
    if not stations and user.role == "station":
        # اولین ایستگاه فعال را برگردان
        stations = SwapStation.query.filter_by(is_active=True).limit(1).all()
    return jsonify({"ok": True, "data": [s.to_dict() for s in stations]})

@bp.get("/<int:station_id>/batteries")
@station_required
def station_batteries(station_id):
    s = SwapStation.query.get_or_404(station_id)
    batteries = Battery.query.filter_by(current_station_id=s.id).all()
    return jsonify({"ok": True, "data": [b.to_dict() for b in batteries]})

@bp.post("/batteries")
@station_required
def add_battery():
    """افزودن باتری جدید به ایستگاه"""
    data = request.get_json() or {}
    b = Battery(
        serial=data["serial"],
        model=data.get("model", "LFP-72V-30Ah"),
        capacity_kwh=float(data.get("capacity_kwh", 3.0)),
        soc=float(data.get("soc", 100.0)),
        soh=float(data.get("soh", 100.0)),
        cycle_count=int(data.get("cycle_count", 0)),
        current_station_id=data.get("station_id"),
        status=data.get("status", "ready"),
    )
    db.session.add(b)
    db.session.commit()
    return jsonify({"ok": True, "data": b.to_dict()}), 201

@bp.patch("/batteries/<int:battery_id>")
@station_required
def update_battery(battery_id):
    b = Battery.query.get_or_404(battery_id)
    data = request.get_json() or {}
    for f in ["soc", "soh", "cycle_count", "temperature_c", "status", "current_station_id"]:
        if f in data:
            setattr(b, f, data[f])
    db.session.commit()
    return jsonify({"ok": True, "data": b.to_dict()})

@bp.post("/<int:station_id>/slots/<int:slot_id>/assign")
@station_required
def assign_slot(station_id, slot_id):
    """اختصاص باتری به اسلات"""
    slot = StationSlot.query.get_or_404(slot_id)
    if slot.station_id != station_id:
        return jsonify({"ok": False, "error": "slot_station_mismatch"}), 400
    data = request.get_json() or {}
    slot.battery_id = data.get("battery_id")
    slot.status = data.get("status", "ready")
    db.session.commit()
    return jsonify({"ok": True, "data": slot.to_dict()})