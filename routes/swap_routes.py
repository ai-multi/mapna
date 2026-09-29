# routes/swap_routes.py
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from sqlalchemy import desc

from models import (
    db, SwapStation, Battery, Vehicle, SwapEvent, StationSlot
)
from auth import login_required, station_required, admin_required, rider_required
from services.pricing import compute_dynamic_price

bp = Blueprint("swap", __name__, url_prefix="/api/swap")

@bp.get("/stations")
@login_required
def list_stations():
    """لیست همه ایستگاه‌های فعال"""
    stations = SwapStation.query.filter_by(is_active=True).all()
    return jsonify({"ok": True, "data": [s.to_dict() for s in stations]})

@bp.get("/stations/<int:station_id>")
@login_required
def get_station(station_id):
    s = SwapStation.query.get_or_404(station_id)
    info = s.to_dict()
    info["slots"] = [sl.to_dict() for sl in s.slots]
    info["ready_batteries"] = sum(
        1 for b in Battery.query.filter_by(current_station_id=s.id, status="ready").all()
    )
    return jsonify({"ok": True, "data": info})

@bp.get("/stations/<int:station_id>/slots")
@login_required
def station_slots(station_id):
    s = SwapStation.query.get_or_404(station_id)
    return jsonify({
        "ok": True,
        "data": [sl.to_dict() for sl in s.slots]
    })

@bp.post("/stations/<int:station_id>/reserve")
@rider_required
def reserve_slot(station_id):
    """رزرو یک باتری آماده در ایستگاه"""
    data = request.get_json() or {}
    user = g.current_user
    vehicle_id = data.get("vehicle_id")

    s = SwapStation.query.get_or_404(station_id)
    if s.available_slots <= 0:
        return jsonify({"ok": False, "error": "no_slots_available"}), 400

    # پیدا کردن بهترین باتری آماده (SoC بالا)
    candidate = (Battery.query
                 .filter(Battery.current_station_id == station_id, Battery.status == "ready")
                 .order_by(desc(Battery.soc))
                 .first())
    if not candidate:
        return jsonify({"ok": False, "error": "no_battery_ready"}), 400

    # محاسبه قیمت پویا
    price_info = compute_dynamic_price(s, candidate.capacity_kwh)

    # ایجاد SwapEvent رزرو
    ev = SwapEvent(
        user_id=user.id,
        vehicle_id=vehicle_id,
        station_id=s.id,
        new_battery_id=candidate.id,
        energy_kwh=candidate.capacity_kwh,
        price_toman=price_info["final_price_toman"],
        status="reserved",
        co2_saved_kg=round(candidate.capacity_kwh * 0.55, 3),
    )
    # باتری رزرو شده، آماده نیست
    candidate.status = "reserved"
    s.available_slots = max(0, s.available_slots - 1)

    # ثبت در اسلات خالی
    empty_slot = StationSlot.query.filter_by(station_id=s.id, status="empty").first()
    if empty_slot:
        empty_slot.battery_id = candidate.id
        empty_slot.status = "reserved"

    db.session.add(ev)
    db.session.commit()

    return jsonify({"ok": True, "data": ev.to_dict(), "price": price_info})

@bp.post("/events/<int:event_id>/complete")
@station_required
def complete_swap(event_id):
    """تأیید تعویض توسط مدیر ایستگاه"""
    ev = SwapEvent.query.get_or_404(event_id)
    if ev.status != "reserved":
        return jsonify({"ok": False, "error": "not_reserved"}), 400

    ev.status = "completed"
    ev.created_at = datetime.utcnow()

    # آزاد کردن باتری قدیمی کاربر (اگر vehicle داشته)
    if ev.vehicle_id and ev.old_battery_id:
        old = Battery.query.get(ev.old_battery_id)
        if old:
            old.current_station_id = ev.station_id
            old.status = "charging"
            old.soc = min(100, old.soc + 10)

    new_battery = Battery.query.get(ev.new_battery_id) if ev.new_battery_id else None
    if new_battery:
        new_battery.status = "in_use"

    # ثبت در اسلات
    slot = StationSlot.query.filter_by(battery_id=new_battery.id).first() if new_battery else None
    if slot:
        slot.status = "ready"

    db.session.commit()
    return jsonify({"ok": True, "data": ev.to_dict()})

@bp.post("/events/<int:event_id>/cancel")
@login_required
def cancel_swap(event_id):
    ev = SwapEvent.query.get_or_404(event_id)
    if ev.user_id != g.current_user.id and g.current_user.role != "admin":
        return jsonify({"ok": False, "error": "forbidden"}), 403
    if ev.status != "reserved":
        return jsonify({"ok": False, "error": "not_reserved"}), 400

    ev.status = "cancelled"
    if ev.new_battery_id:
        b = Battery.query.get(ev.new_battery_id)
        if b:
            b.status = "ready"
    s = SwapStation.query.get(ev.station_id)
    if s:
        s.available_slots = min(s.capacity_slots, s.available_slots + 1)
    slot = StationSlot.query.filter_by(battery_id=ev.new_battery_id).first() if ev.new_battery_id else None
    if slot:
        slot.battery_id = None
        slot.status = "empty"
    db.session.commit()
    return jsonify({"ok": True})

@bp.get("/events")
@login_required
def list_events():
    user = g.current_user
    q = SwapEvent.query
    if user.role == "rider":
        q = q.filter_by(user_id=user.id)
    elif user.role == "station":
        sids = [s.id for s in SwapStation.query.filter_by(manager_id=user.id).all()]
        q = q.filter(SwapEvent.station_id.in_(sids))
    events = q.order_by(desc(SwapEvent.created_at)).limit(50).all()
    return jsonify({"ok": True, "data": [e.to_dict() for e in events]})

@bp.post("/price-preview")
@login_required
def price_preview():
    data = request.get_json() or {}
    station_id = data.get("station_id")
    energy = float(data.get("energy_kwh") or 3.0)
    s = SwapStation.query.get_or_404(station_id)
    info = compute_dynamic_price(s, energy)
    return jsonify({"ok": True, "data": info})

@bp.post("/stations")
@admin_required
def create_station():
    data = request.get_json() or {}
    s = SwapStation(
        name=data["name"],
        address=data.get("address"),
        lat=float(data["lat"]),
        lng=float(data["lng"]),
        capacity_slots=int(data.get("capacity_slots", 20)),
        available_slots=int(data.get("capacity_slots", 20)),
        fast_charge_kw=float(data.get("fast_charge_kw", 22.0)),
        opening_hour=int(data.get("opening_hour", 0)),
        closing_hour=int(data.get("closing_hour", 23)),
    )
    db.session.add(s)
    db.session.commit()

    # ساخت اسلات‌ها
    for i in range(s.capacity_slots):
        sl = StationSlot(station_id=s.id, slot_code=f"S{i+1:02d}", status="empty")
        db.session.add(sl)
    db.session.commit()
    return jsonify({"ok": True, "data": s.to_dict()}), 201