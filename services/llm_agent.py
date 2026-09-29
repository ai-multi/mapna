# services/llm_agent.py
"""AI Assistant: Mock (rule-based) + AVALAI integration."""
import re
import json
import requests
from datetime import datetime
from sqlalchemy import desc
from models import db, Battery, SwapStation, MaintenanceTicket, ChatMessage, Vehicle
from services import routing, predictions, analytics
from config import Config

INTENT_KEYWORDS = {
    "find_station": ["ايستگاه", "پمپ", "جايگاه", "station", "find station"],
    "battery_health": ["سلامت باتري", "soh", "soc", "battery", "باتري"],
    "trip_history": ["تاريخچه سفر", "trip history", "سفرهاي من"],
    "cost_analysis": ["هزينه", "قبض", "خرج", "cost", "expense", "تحليل هزينه"],
    "maintenance": ["سرويس", "نگهداري", "تعمير", "maintenance"],
    "eco_tips": ["اکو", "محيط زيست", "صرفه", "eco", "green", "کربن"],
    "route": ["مسير", "مسيريابي", "route", "navigation", "راهنما"],
    "sos": ["کمک", "اضطراري", "خراب شد", "sos", "emergency"],
    "charger_status": ["شارژر", "charger", "اسلات"],
    "fleet_status": ["ناوگان", "fleet"],
    "sla_support": ["پشتيباني", "sla", "support", "ticket"],
    "in_mission": ["در ماموريت", "in mission"],
    "in_service": ["در سرويس", "in service"],
    "downtime": ["downtime", "داون تايم", "خاموشي"],
    "uptime": ["uptime", "آپ تايم"],
    "pilot_count": ["پايلوت", "pilot"],
    "ready_count": ["آماده سرويس", "ready"],
    "recent_alerts": ["هشدار", "alert", "خرابي اخير"],
    "vehicle_status": ["وضعيت موتور", "vehicle status"],
    "battery_soc": ["شارژ باتري", "battery soc"],
    "avg_soc": ["ميانگين soc", "avg soc", "ميانگين شارژ"],
}

def detect_intent(text):
    t = (text or "").lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in t:
                return intent
    return "general"

def _nearest_stations(user, text):
    lat, lng = 35.6892, 51.3890
    m = re.search(r"lat[:\s]+(-?\d+\.?\d*)[,\s]+lng[:\s]+(-?\d+\.?\d*)", text)
    if m:
        lat = float(m.group(1))
        lng = float(m.group(2))
    pref = "balanced"
    if "سریع" in text or "fast" in text:
        pref = "fastest"
    elif "ارزان" in text or "cheap" in text:
        pref = "cheapest"
    elif "ظرفیت" in text or "available" in text:
        pref = "available"
    plan = routing.plan_route(lat, lng, soc_percent=60, weather="clear", preference=pref)
    return {"intent": "find_station", "message": "نزدیک‌ترین ایستگاه‌ها", "data": plan}

def _battery_health(user, text):
    items = []
    for b in Battery.query.limit(10).all():
        p = predictions.predict_battery_failure(b)
        items.append({"serial": b.serial, "soc": b.soc, "soh": b.soh, "cycles": b.cycle_count, "risk": p["risk_level"]})
    return {"intent": "battery_health", "message": "گزارش سلامت باتری‌ها", "data": items}

def _trip_history(user, text):
    days = 30
    m = re.search(r"(\d+)\s*(روز|day)", text)
    if m:
        days = int(m.group(1))
    return {"intent": "trip_history", "message": "تاریخچه " + str(days) + " روز اخیر", "data": analytics.rider_history(user.id, days=days)}

def _cost_analysis(user, text):
    h = analytics.rider_history(user.id, days=30)
    avg = int(h["total_cost_toman"] / max(1, h["trip_count"]))
    return {"intent": "cost_analysis", "message": "تحلیل هزینه ۳۰ روز اخیر", "data": {
        "total_cost_toman": h["total_cost_toman"], "trip_count": h["trip_count"],
        "swap_count": h["swap_count"], "avg_cost_per_trip": avg}}

def _maintenance(user, text):
    tickets = MaintenanceTicket.query.filter(MaintenanceTicket.status.in_(["open", "in_progress"])).limit(10).all()
    return {"intent": "maintenance", "message": str(len(tickets)) + " تیکت فعال", "data": [t.to_dict() for t in tickets]}

def _eco_tips(user, text):
    h = analytics.rider_history(user.id, days=30)
    return {"intent": "eco_tips", "message": "نکات اکو و صرفه‌جویی", "data": {
        "co2_saved_kg": h["co2_saved_kg"],
        "tips": ["در ترافیک سنگین از ریژن استفاده کنید", "فشار باد تایر را ماهیانه چک کنید", "از ایستگاه‌های نزدیک استفاده کنید"]}}

def _route(user, text):
    plan = routing.plan_route(35.6892, 51.3890, 35.7589, 51.4159, soc_percent=60)
    return {"intent": "route", "message": "پیشنهاد مسیر", "data": plan}

def _sos(user, text):
    return {"intent": "sos", "message": "SOS ثبت شد. تیم پشتیبانی تماس می‌گیرد.", "data": {
        "user_id": user.id, "phone": user.phone, "timestamp": datetime.utcnow().isoformat(),
        "next_steps": ["تیم عملیات در 5 دقیقه تماس می‌گیرد", "موقعیت شما ارسال شد", "در خطر فوری با 115 تماس بگیرید"]}}

def _charger_status(user, text):
    out = []
    for s in SwapStation.query.all():
        ready = Battery.query.filter(Battery.current_station_id == s.id, Battery.status == "ready").count()
        charging = Battery.query.filter(Battery.current_station_id == s.id, Battery.status == "charging").count()
        out.append({"station_id": s.id, "station_name": s.name, "available_slots": s.available_slots,
                    "capacity_slots": s.capacity_slots, "batteries_ready": ready, "batteries_charging": charging})
    return {"intent": "charger_status", "message": "وضعیت شارژرها و اسلات‌ها", "data": out}

def _fleet_status(user, text):
    return {"intent": "fleet_status", "message": "خلاصه وضعیت ناوگان", "data": analytics.fleet_health()}

def _sla_support(user, text):
    tickets = MaintenanceTicket.query.filter(MaintenanceTicket.status.in_(["open", "in_progress"])).all()
    return {"intent": "sla_support", "message": str(len(tickets)) + " تیکت باز", "data": {
        "open": len(tickets), "critical": sum(1 for t in tickets if t.severity == "critical"),
        "tickets": [t.to_dict() for t in tickets[:5]]}}

def _count(status=None, in_pilot=None):
    q = Vehicle.query
    if status:
        q = q.filter_by(status=status)
    if in_pilot is not None:
        q = q.filter_by(in_pilot=in_pilot)
    return q.count()

def _in_mission(user, text):
    n = _count(status="in_service")
    return {"intent": "in_mission", "message": str(n) + " وسیله در ماموریت فعال", "data": {"count": n}}

def _in_service(user, text):
    n = _count(status="in_service")
    return {"intent": "in_service", "message": str(n) + " وسیله در سرویس", "data": {"count": n}}

def _downtime(user, text):
    ov = analytics.overview()
    return {"intent": "downtime", "message": "Downtime: " + str(round(ov["vehicles"]["downtime_ratio"]*100, 1)) + "%", "data": ov["vehicles"]}

def _uptime(user, text):
    ov = analytics.overview()
    return {"intent": "uptime", "message": "Uptime: " + str(round(ov["vehicles"]["uptime_ratio"]*100, 1)) + "%", "data": ov["vehicles"]}

def _pilot_count(user, text):
    n = _count(in_pilot=True)
    return {"intent": "pilot_count", "message": str(n) + " موتور در فاز پایلوت", "data": {"count": n}}

def _ready_count(user, text):
    n = _count(status="ready")
    return {"intent": "ready_count", "message": str(n) + " موتور آماده سرویس", "data": {"count": n}}

def _recent_alerts(user, text):
    return {"intent": "recent_alerts", "message": "هشدارها و خرابی‌های اخیر", "data": analytics.recent_alerts(10)}

def _vehicle_status(user, text):
    statuses = {}
    for v in Vehicle.query.all():
        statuses[v.status] = statuses.get(v.status, 0) + 1
    return {"intent": "vehicle_status", "message": "وضعیت موتورها", "data": statuses}

def _battery_soc(user, text):
    batteries = Battery.query.limit(20).all()
    items = [{"serial": b.serial, "soc": b.soc, "soh": b.soh, "status": b.status} for b in batteries]
    avg = sum(b.soc for b in batteries) / len(batteries) if batteries else 0
    return {"intent": "battery_soc", "message": "میانگین SoC: " + str(round(avg, 1)) + "%", "data": {"average_soc": round(avg, 1), "items": items}}

def _avg_soc(user, text):
    res = db.session.query(db.func.avg(Battery.soc)).filter(Battery.status.in_(["ready", "charging"])).scalar() or 0
    return {"intent": "avg_soc", "message": "میانگین SoC کل: " + str(round(res, 1)) + "%", "data": {"average_soc": round(res, 1)}}

def _general(user, text):
    return {"intent": "general", "message": "من می‌توانم کمکتان کنم: ایستگاه، باتری، سفر، هزینه، سرویس، اکو، مسیر، SOS. لطفاً سوال را دقیق‌تر بپرسید.", "data": {}}

HANDLERS = {
    "find_station": _nearest_stations, "battery_health": _battery_health,
    "trip_history": _trip_history, "cost_analysis": _cost_analysis,
    "maintenance": _maintenance, "eco_tips": _eco_tips, "route": _route,
    "sos": _sos, "charger_status": _charger_status, "fleet_status": _fleet_status,
    "sla_support": _sla_support, "in_mission": _in_mission, "in_service": _in_service,
    "downtime": _downtime, "uptime": _uptime, "pilot_count": _pilot_count,
    "ready_count": _ready_count, "recent_alerts": _recent_alerts,
    "vehicle_status": _vehicle_status, "battery_soc": _battery_soc,
    "avg_soc": _avg_soc, "general": _general,
}

def mock_respond(user, text, intent, handler_result):
    msg = handler_result.get("message", "")
    data = handler_result.get("data", {}) or {}

    if intent == "find_station":
        rec = data.get("recommended")
        cands = data.get("candidates", []) or []
        if not rec:
            return "⚠️ " + msg + "\nایستگاهی در شعاع باتری شما پیدا نشد."
        lines = ["📍 " + msg, "پیشنهاد: " + rec["station_name"] + " (" + str(rec["distance_km"]) + " km)"]
        for i, c in enumerate(cands[:5], 1):
            lines.append(str(i) + ". " + c["station_name"] + " — " + str(c["distance_km"]) + " km | خالی: " + str(c["available_slots"]) + " | امتیاز: " + str(c["score"]))
        return "\n".join(lines)

    if intent == "battery_health":
        lines = ["🔋 " + msg]
        for b in (data or [])[:5]:
            lines.append("• " + b["serial"] + ": SoC=" + str(round(b["soc"],0)) + " SoH=" + str(round(b["soh"],0)) + " ریسک=" + b["risk"])
        return "\n".join(lines)

    if intent == "trip_history":
        return "📊 " + msg + "\nسفر: " + str(data.get("trip_count",0)) + " | مسافت: " + str(data.get("total_distance_km",0)) + " km | CO₂: " + str(data.get("co2_saved_kg",0)) + " kg"

    if intent == "cost_analysis":
        return "💰 " + msg + "\nهزینه کل: " + str(data.get("total_cost_toman",0)) + " تومان\nمیانگین/سفر: " + str(data.get("avg_cost_per_trip",0)) + " تومان"

    if intent == "maintenance":
        lines = ["🛠 " + msg]
        for t in (data or [])[:5]:
            lines.append("• [" + t["severity"] + "] " + t["title"])
        return "\n".join(lines)

    if intent == "eco_tips":
        tips = "\n".join("• " + t for t in (data.get("tips") or []))
        return "🌱 " + msg + "\nCO₂: " + str(data.get("co2_saved_kg",0)) + " kg\n" + tips

    if intent == "route":
        rec = data.get("recommended")
        if rec:
            return "🗺 " + msg + "\n" + rec["station_name"] + " | ETA: " + str(data.get("eta_minutes")) + " دقیقه"
        return "⚠️ مسیر مناسب نیست."

    if intent == "sos":
        steps = "\n".join("• " + s for s in (data.get("next_steps") or []))
        return "🚨 " + msg + "\n" + steps

    if intent == "charger_status":
        lines = ["🔌 " + msg]
        for s in data:
            lines.append("• " + s["station_name"] + ": " + str(s["available_slots"]) + "/" + str(s["capacity_slots"]) + " | آماده: " + str(s["batteries_ready"]))
        return "\n".join(lines)

    if intent == "fleet_status":
        return "🚚 " + msg + "\nموتور: " + str(data.get("vehicle_count",0)) + " | سرویس نزدیک: " + str(data.get("service_due_count",0))

    if intent == "sla_support":
        return "📞 " + msg + "\nبحرانی: " + str(data.get("critical",0))

    if intent in ("in_mission", "in_service", "pilot_count", "ready_count"):
        return "📈 " + msg + " → " + str(data.get("count",0))

    if intent in ("downtime", "uptime"):
        return "⏱ " + msg + "\nUptime: " + str(round(data.get("uptime_ratio",0)*100, 1)) + "% | Downtime: " + str(round(data.get("downtime_ratio",0)*100, 1)) + "%"

    if intent == "recent_alerts":
        lines = ["⚠️ " + msg]
        for a in (data or [])[:5]:
            lines.append("• [" + str(a.get("severity")) + "] " + str(a.get("title")))
        return "\n".join(lines)

    if intent == "vehicle_status":
        lines = ["🏍 " + msg]
        for k, v in (data or {}).items():
            lines.append("• " + str(k) + ": " + str(v))
        return "\n".join(lines)

    if intent in ("battery_soc", "avg_soc"):
        return "🔋 " + msg

    return msg + "\n" + json.dumps(data, ensure_ascii=False)[:300]

def avalai_respond(user, text, system_context):
    if not Config.AVALAI_API_KEY:
        return None
    try:
        resp = requests.post(
            Config.AVALAI_BASE_URL + "/chat/completions",
            headers={"Authorization": "Bearer " + Config.AVALAI_API_KEY, "Content-Type": "application/json"},
            json={"model": Config.AVALAI_MODEL, "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": text}], "temperature": 0.3, "max_tokens": 500},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None

def ask(user, text, use_avalai=False):
    intent = detect_intent(text)
    handler = HANDLERS.get(intent, HANDLERS["general"])
    result = handler(user, text)

    db.session.add(ChatMessage(user_id=user.id, role="user", content=text, intent=intent))

    response_text = None
    if use_avalai and Config.AVALAI_API_KEY:
        ctx = "دستیار MAPNA SwapFleet AI. فارسی پاسخ بده. نقش: " + user.role + ". داده: " + json.dumps(result.get("data", {}), ensure_ascii=False)[:800]
        response_text = avalai_respond(user, text, ctx)

    if not response_text:
        response_text = mock_respond(user, text, intent, result)

    db.session.add(ChatMessage(user_id=user.id, role="assistant", content=response_text, intent=intent))
    db.session.commit()

    return {
        "ok": True, "intent": intent, "reply": response_text,
        "data": result.get("data"),
        "source": "avalai" if (use_avalai and Config.AVALAI_API_KEY and response_text) else "mock",
    }

def chat_history(user_id, limit=50):
    msgs = (ChatMessage.query.filter_by(user_id=user_id)
            .order_by(desc(ChatMessage.created_at)).limit(limit).all())
    return [m.to_dict() for m in reversed(msgs)]