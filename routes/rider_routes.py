# routes/rider_routes.py
from flask import Blueprint, jsonify, g
from auth import rider_required
from models import Vehicle, Trip, SwapEvent
from services import analytics

bp = Blueprint("rider", __name__, url_prefix="/api/rider")

@bp.get("/dashboard")
@rider_required
def dashboard():
    user = g.current_user
    vehicles = Vehicle.query.filter_by(owner_id=user.id).all()
    recent_trips = (Trip.query.filter_by(rider_id=user.id)
                    .order_by(Trip.started_at.desc()).limit(5).all())
    recent_swaps = (SwapEvent.query.filter_by(user_id=user.id)
                    .order_by(SwapEvent.created_at.desc()).limit(5).all())
    h = analytics.rider_history(user.id, days=30)
    return jsonify({
        "ok": True,
        "data": {
            "vehicles": [v.to_dict() for v in vehicles],
            "recent_trips": [t.to_dict() for t in recent_trips],
            "recent_swaps": [s.to_dict() for s in recent_swaps],
            "summary": {
                "trip_count": h["trip_count"],
                "swap_count": h["swap_count"],
                "total_distance_km": h["total_distance_km"],
                "total_cost_toman": h["total_cost_toman"],
                "co2_saved_kg": h["co2_saved_kg"],
            },
        }
    })

@bp.get("/vehicles")
@rider_required
def my_vehicles():
    user = g.current_user
    return jsonify({"ok": True, "data": [v.to_dict() for v in Vehicle.query.filter_by(owner_id=user.id).all()]})