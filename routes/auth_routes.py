# routes/auth_routes.py
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token
from models import User, db
from auth import login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    if not user.is_active:
        return jsonify({"ok": False, "error": "user_inactive"}), 403

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )
    return jsonify({
        "ok": True,
        "token": token,
        "user": user.to_dict(),
    })

@bp.post("/register")
def register():
    """فقط برای تست - ثبت‌نام با نقش دلخواه (در تولید باید محدود شود)"""
    data = request.get_json() or {}
    required = ["email", "password", "full_name", "role"]
    for k in required:
        if not data.get(k):
            return jsonify({"ok": False, "error": f"missing_{k}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"ok": False, "error": "email_exists"}), 409

    user = User(
        email=data["email"].strip().lower(),
        full_name=data["full_name"],
        role=data["role"],
        phone=data.get("phone"),
        company_id=data.get("company_id"),
        home_station_id=data.get("home_station_id"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"ok": True, "user": user.to_dict()}), 201

@bp.get("/me")
@login_required
def me():
    return jsonify({"ok": True, "user": g.current_user.to_dict()})