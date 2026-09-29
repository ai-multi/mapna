# routes/route_routes.py
from flask import Blueprint, request, jsonify
from auth import login_required
from services.routing import plan_route, haversine_km

bp = Blueprint("route", __name__, url_prefix="/api/route")

@bp.post("/plan")
@login_required
def plan():
    data = request.get_json() or {}
    origin_lat = float(data.get("origin_lat", 35.6892))
    origin_lng = float(data.get("origin_lng", 51.3890))
    dest_lat = data.get("dest_lat")
    dest_lng = data.get("dest_lng")
    soc = float(data.get("soc_percent", 60.0))
    weather = data.get("weather", "clear")
    preference = data.get("preference", "balanced")

    plan_data = plan_route(
        origin_lat, origin_lng,
        dest_lat=dest_lat, dest_lng=dest_lng,
        soc_percent=soc, weather=weather, preference=preference,
    )
    return jsonify({"ok": True, "data": plan_data})

@bp.get("/distance")
@login_required
def distance():
    lat1 = float(request.args.get("lat1", 0))
    lng1 = float(request.args.get("lng1", 0))
    lat2 = float(request.args.get("lat2", 0))
    lng2 = float(request.args.get("lng2", 0))
    d = haversine_km(lat1, lng1, lat2, lng2)
    return jsonify({"ok": True, "data": {"distance_km": d}})