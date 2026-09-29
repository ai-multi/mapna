# routes/analytics_routes.py
from flask import Blueprint, request, jsonify, g
from auth import login_required, admin_required, station_required, fleet_required
from services import analytics, predictions

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@bp.get("/overview")
@admin_required
def overview():
    return jsonify({"ok": True, "data": analytics.overview()})

@bp.get("/stations")
@admin_required
def station_perf():
    return jsonify({"ok": True, "data": analytics.station_performance()})

@bp.get("/fleet")
@fleet_required
def fleet_health():
    company_id = request.args.get("company_id", type=int) or (
        g.current_user.company_id if g.current_user.role == "fleet" else None
    )
    return jsonify({"ok": True, "data": analytics.fleet_health(company_id=company_id)})

@bp.get("/predictions/batteries")
@login_required
def predict_batteries():
    return jsonify({"ok": True, "data": predictions.scan_fleet_predictions()})

@bp.get("/predictions/vehicles")
@fleet_required
def predict_vehicles():
    company_id = (
        g.current_user.company_id if g.current_user.role == "fleet" else None
    )
    fleet = analytics.fleet_health(company_id=company_id)
    out = []
    for v in fleet.get("vehicles", []):
        from models import Vehicle
        veh = Vehicle.query.get(v["id"])
        if veh:
            out.append(predictions.predict_vehicle_service(veh))
    return jsonify({"ok": True, "data": out})

@bp.get("/alerts")
@login_required
def alerts():
    return jsonify({"ok": True, "data": analytics.recent_alerts(20)})

@bp.get("/recent-swaps")
@login_required
def recent_swaps():
    return jsonify({"ok": True, "data": analytics.recent_swaps(20)})

@bp.get("/rider/<int:rider_id>")
@login_required
def rider_stats(rider_id):
    user = g.current_user
    if user.role == "rider" and user.id != rider_id:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    days = request.args.get("days", default=30, type=int)
    return jsonify({"ok": True, "data": analytics.rider_history(rider_id, days=days)})