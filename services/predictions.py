# services/predictions.py
from datetime import datetime, timedelta
from models import Battery, Vehicle, MaintenanceTicket

def predict_battery_failure(battery: Battery) -> dict:
    """
    پیش‌بینی ریسک خرابی باتری:
      - soh پایین
      - cycle_count زیاد
      - دمای بالا
      - زمان طولانی از آخرین شارژ کامل
    """
    reasons = []
    risk = battery.predicted_failure_risk()

    if battery.soh < 70:
        reasons.append(f"SoH پایین ({battery.soh:.1f}%) — نیاز به بررسی سلول‌ها")
    if battery.soh < 85:
        reasons.append(f"SoH در محدوده هشدار ({battery.soh:.1f}%)")

    if battery.cycle_count > 1200:
        reasons.append(f"چرخه شارژ بالا ({battery.cycle_count}) — نزدیک به پایان عمر")
    elif battery.cycle_count > 800:
        reasons.append(f"چرخه شارژ قابل توجه ({battery.cycle_count})")

    if battery.temperature_c > 50:
        reasons.append(f"دمای بحرانی ({battery.temperature_c:.1f}°C)")
    elif battery.temperature_c > 45:
        reasons.append(f"دمای بالا ({battery.temperature_c:.1f}°C)")

    if battery.last_charged_at:
        hours_since = (datetime.utcnow() - battery.last_charged_at).total_seconds() / 3600
        if hours_since > 240:
            reasons.append(f"بیش از {int(hours_since/24)} روز از آخرین شارژ کامل گذشته")

    # ایجاد تیکت خودکار در صورت ریسک بالا
    auto_ticket = False
    if risk >= 0.6 and battery.status != "fault":
        existing = MaintenanceTicket.query.filter_by(
            battery_id=battery.id,
            predicted=True,
        ).filter(MaintenanceTicket.status.in_(["open", "in_progress"])).first()
        if not existing:
            auto_ticket = True

    return {
        "battery_id": battery.id,
        "serial": battery.serial,
        "soh": battery.soh,
        "cycle_count": battery.cycle_count,
        "temperature_c": battery.temperature_c,
        "risk_score": risk,
        "risk_level": (
            "critical" if risk >= 0.7
            else "high" if risk >= 0.45
            else "medium" if risk >= 0.2
            else "low"
        ),
        "reasons": reasons,
        "auto_create_ticket": auto_ticket,
    }

def predict_vehicle_service(vehicle: Vehicle) -> dict:
    """پیش‌بینی نیاز به سرویس دوره‌ای وسیله نقلیه"""
    km_to_service = vehicle.km_to_next_service()
    pct = max(0.0, km_to_service / vehicle.service_interval_km * 100)

    risk = 0.0
    reasons = []

    if km_to_service == 0:
        risk = 1.0
        reasons.append("سرویس دوره‌ای سررسید شده است")
    elif km_to_service < 200:
        risk = 0.85
        reasons.append(f"کمتر از 200 کیلومتر تا سرویس بعدی ({km_to_service:.0f} km)")
    elif km_to_service < 500:
        risk = 0.5
        reasons.append(f"نزدیک به سرویس ({km_to_service:.0f} km باقی مانده)")

    if vehicle.status == "fault":
        risk = max(risk, 0.9)
        reasons.append("وضعیت خودرو: خرابی گزارش شده")

    return {
        "vehicle_id": vehicle.id,
        "plate": vehicle.plate,
        "odometer_km": vehicle.odometer_km,
        "km_to_service": km_to_service,
        "service_interval_km": vehicle.service_interval_km,
        "percent_remaining": round(pct, 1),
        "risk_score": round(risk, 3),
        "risk_level": (
            "critical" if risk >= 0.8
            else "high" if risk >= 0.45
            else "medium" if risk >= 0.2
            else "low"
        ),
        "reasons": reasons,
        "status": vehicle.status,
    }

def scan_fleet_predictions(vehicle_ids=None) -> dict:
    """اسکن کل ناوگان برای پیش‌بینی‌ها"""
    batteries = Battery.query.all()
    vehicles = (
        Vehicle.query.filter(Vehicle.id.in_(vehicle_ids)).all()
        if vehicle_ids else Vehicle.query.all()
    )

    battery_risks = [predict_battery_failure(b) for b in batteries]
    vehicle_risks = [predict_vehicle_service(v) for v in vehicles]

    battery_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    vehicle_risks.sort(key=lambda x: x["risk_score"], reverse=True)

    # ایجاد خودکار تیکت‌های پیش‌بینی‌شده
    new_tickets = 0
    for r in battery_risks:
        if r["auto_create_ticket"]:
            b = Battery.query.get(r["battery_id"])
            t = MaintenanceTicket(
                battery_id=b.id,
                title=f"پیش‌بینی خرابی باتری {b.serial}",
                description=" | ".join(r["reasons"]) or "نیاز به بررسی",
                severity="high" if r["risk_score"] >= 0.7 else "medium",
                status="open",
                predicted=True,
            )
            from models import db
            db.session.add(t)
            new_tickets += 1
    if new_tickets:
        db.session.commit()

    return {
        "battery_predictions": battery_risks[:10],
        "vehicle_predictions": vehicle_risks[:10],
        "summary": {
            "total_batteries": len(batteries),
            "high_risk_batteries": sum(1 for r in battery_risks if r["risk_score"] >= 0.5),
            "total_vehicles": len(vehicles),
            "service_due_vehicles": sum(1 for r in vehicle_risks if r["risk_score"] >= 0.5),
            "new_tickets_created": new_tickets,
        },
    }