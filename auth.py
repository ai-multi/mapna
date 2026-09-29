# auth.py
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt, get_jwt_identity
)
from models import User

def login_required(fn):
    """نیاز به JWT معتبر"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({"ok": False, "error": "auth_required", "message": str(e)}), 401

        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            return jsonify({"ok": False, "error": "user_inactive"}), 401
        g.current_user = user
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    """نیاز به نقش خاص - مثلاً @role_required('admin')"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                return jsonify({"ok": False, "error": "auth_required", "message": str(e)}), 401

            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({
                    "ok": False,
                    "error": "forbidden",
                    "message": f"نقش {user_role} مجاز نیست. نقش‌های مجاز: {roles}"
                }), 403

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user or not user.is_active:
                return jsonify({"ok": False, "error": "user_inactive"}), 401
            g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    return role_required("admin")(fn)

def station_required(fn):
    return role_required("admin", "station")(fn)

def fleet_required(fn):
    return role_required("admin", "fleet")(fn)

def rider_required(fn):
    return role_required("admin", "rider", "fleet", "station")(fn)