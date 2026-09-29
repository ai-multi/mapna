# routes/admin_routes.py
from flask import Blueprint, request, jsonify, g
from sqlalchemy import desc
from auth import admin_required
from models import db, User, Company, Vehicle, Battery, MaintenanceTicket, SwapStation

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@bp.get("/users")
@admin_required
def list_users():
    users = User.query.order_by(desc(User.created_at)).all()
    return jsonify({"ok": True, "data": [u.to_dict() for u in users]})

@bp.post("/users")
@admin_required
def create_user():
    data = request.get_json() or {}
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"ok": False, "error": "email_exists"}), 409
    u = User(
        email=data["email"],
        full_name=data["full_name"],
        role=data["role"],
        phone=data.get("phone"),
        company_id=data.get("company_id"),
        home_station_id=data.get("home_station_id"),
    )
    u.set_password(data.get("password", "123456"))
    db.session.add(u)
    db.session.commit()
    return jsonify({"ok": True, "data": u.to_dict()}), 201

@bp.patch("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    u = User.query.get_or_404(user_id)
    u.is_active = not u.is_active
    db.session.commit()
    return jsonify({"ok": True, "data": u.to_dict()})

@bp.get("/companies")
@admin_required
def list_companies():
    return jsonify({"ok": True, "data": [c.to_dict() for c in Company.query.all()]})

@bp.post("/companies")
@admin_required
def create_company():
    data = request.get_json() or {}
    c = Company(
        name=data["name"],
        tax_id=data.get("tax_id"),
        contact_phone=data.get("contact_phone"),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True, "data": c.to_dict()}), 201

@bp.get("/tickets")
@admin_required
def list_tickets():
    tickets = MaintenanceTicket.query.order_by(desc(MaintenanceTicket.created_at)).limit(50).all()
    return jsonify({"ok": True, "data": [t.to_dict() for t in tickets]})

@bp.patch("/tickets/<int:ticket_id>")
@admin_required
def update_ticket(ticket_id):
    t = MaintenanceTicket.query.get_or_404(ticket_id)
    data = request.get_json() or {}
    if "status" in data:
        t.status = data["status"]
        if data["status"] == "resolved":
            from datetime import datetime
            t.resolved_at = datetime.utcnow()
    if "severity" in data:
        t.severity = data["severity"]
    db.session.commit()
    return jsonify({"ok": True, "data": t.to_dict()})

@bp.get("/stations")
@admin_required
def all_stations():
    return jsonify({"ok": True, "data": [s.to_dict() for s in SwapStation.query.all()]})