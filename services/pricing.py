# services/pricing.py
from datetime import datetime
from models import PriceRule, SwapStation
from config import Config

def compute_dynamic_price(station: SwapStation, energy_kwh: float, dt: datetime = None) -> dict:
    """
    محاسبه قیمت پویا بر اساس:
      - ساعت و روز هفته (PriceRule)
      - ضریب تقاضا (اشغال ایستگاه)
      - قیمت پایه (Config.BASE_PRICE_PER_KWH)
    خروجی: dict شامل قیمت نهایی، ضریب‌ها، توضیح.
    """
    dt = dt or datetime.utcnow()
    weekday = dt.weekday()  # Mon=0..Sun=6
    hour = dt.hour

    base_price = energy_kwh * Config.BASE_PRICE_PER_KWH

    # انتخاب بهترین قانون (priority بالاتر اولویت دارد)
    rules = (
        PriceRule.query.filter_by(station_id=station.id)
        .order_by(PriceRule.priority.desc())
        .all()
    )
    matched_rule = None
    for r in rules:
        if r.matches(weekday, hour):
            matched_rule = r
            break

    multiplier = matched_rule.multiplier if matched_rule else 1.0

    # ضریب تقاضا بر اساس اشغال ایستگاه
    occ = station.occupancy_ratio()  # 0..1
    if occ < 0.3:
        demand_factor = 0.9
    elif occ < 0.6:
        demand_factor = 1.0
    elif occ < 0.85:
        demand_factor = 1.15
    else:
        demand_factor = 1.3

    # اگر خارج از ساعت کاری، 10% اضافه
    after_hours = hour < station.opening_hour or hour > station.closing_hour
    if after_hours:
        multiplier *= 1.10

    final_price = round(base_price * multiplier * demand_factor, 0)

    return {
        "station_id": station.id,
        "station_name": station.name,
        "energy_kwh": energy_kwh,
        "base_price_toman": round(base_price, 0),
        "multiplier": round(multiplier, 3),
        "demand_factor": round(demand_factor, 3),
        "occupancy_ratio": occ,
        "final_price_toman": int(final_price),
        "matched_rule_id": matched_rule.id if matched_rule else None,
        "hour": hour,
        "weekday": weekday,
        "after_hours": after_hours,
    }