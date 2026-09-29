# routes/llm_routes.py
from flask import Blueprint, request, jsonify, g
from auth import login_required
from services.llm_agent import ask, chat_history

bp = Blueprint("llm", __name__, url_prefix="/api/llm")

@bp.post("/ask")
@login_required
def llm_ask():
    data = request.get_json() or {}
    text = (data.get("message") or "").strip()
    use_avalai = bool(data.get("use_avalai", False))

    if not text:
        return jsonify({"ok": False, "error": "empty_message"}), 400

    result = ask(g.current_user, text, use_avalai=use_avalai)
    return jsonify(result)

@bp.get("/history")
@login_required
def llm_history():
    return jsonify({"ok": True, "data": chat_history(g.current_user.id, limit=80)})