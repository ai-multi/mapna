# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

# ============================================================
# Company (شرکت)
# ============================================================
class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    tax_id = db.Column(db.String(50), unique=True)
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", backref="company", lazy=True)
    vehicles = db.relationship("Vehicle", backref="company", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tax_id": self.tax_id,
            "contact_phone": self.contact_phone,
            "user_count": len(self.users),
            "vehicle_count": len(self.vehicles),
        }

# ============================================================
# User
# ============================================================
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, station, fleet, rider
    phone = db.Column(db.String(20))
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    home_station_id = db.Column(
        db.Integer,
        db.ForeignKey("swap_stations.id", use_alter=True, name="fk_user_home_station"),
        nullable=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    vehicles = db.relationship("Vehicle", backref="owner", lazy=True)
    trips = db.relationship("Trip", backref="rider", lazy=True)
    swap_events = db.relationship("SwapEvent", backref="user", lazy=True)

    def set_password(self, raw):
        self.password_hash = bcrypt.generate_password_hash(raw).decode("utf-8")

    def check_password(self, raw):
        return bcrypt.check_password_hash(self.password_hash, raw)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "phone": self.phone,
            "company_id": self.company_id,
            "home_station_id": self.home_station_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }# ============================================================
# SwapStation
# ============================================================
class SwapStation(db.Model):
    __tablename__ = "swap_stations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255))
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    capacity_slots = db.Column(db.Integer, default=20)
    available_slots = db.Column(db.Integer, default=20)
    fast_charge_kw = db.Column(db.Float, default=22.0)
    is_active = db.Column(db.Boolean, default=True)
    opening_hour = db.Column(db.Integer, default=0)   # 0..23
    closing_hour = db.Column(db.Integer, default=23)  # 0..23
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship("User", foreign_keys=[manager_id])
    slots = db.relationship("StationSlot", backref="station", lazy=True, cascade="all, delete-orphan")
    batteries = db.relationship("Battery", backref="current_station", lazy=True)
    price_rules = db.relationship("PriceRule", backref="station", lazy=True, cascade="all, delete-orphan")
    swap_events = db.relationship("SwapEvent", backref="station", lazy=True)

    def occupancy_ratio(self):
        if self.capacity_slots == 0:
            return 0.0
        return round(1.0 - (self.available_slots / self.capacity_slots), 3)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "capacity_slots": self.capacity_slots,
            "available_slots": self.available_slots,
            "fast_charge_kw": self.fast_charge_kw,
            "is_active": self.is_active,
            "opening_hour": self.opening_hour,
            "closing_hour": self.closing_hour,
            "manager_id": self.manager_id,
            "occupancy_ratio": self.occupancy_ratio(),
        }

# ============================================================
# StationSlot
# ============================================================
class StationSlot(db.Model):
    __tablename__ = "station_slots"
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey("swap_stations.id"), nullable=False)
    slot_code = db.Column(db.String(20), nullable=False)
    battery_id = db.Column(db.Integer, db.ForeignKey("batteries.id"), nullable=True)
    status = db.Column(db.String(20), default="empty")  # empty, charging, ready, fault
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    battery = db.relationship("Battery", foreign_keys=[battery_id])

    def to_dict(self):
        return {
            "id": self.id,
            "station_id": self.station_id,
            "slot_code": self.slot_code,
            "battery_id": self.battery_id,
            "status": self.status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }# ============================================================
# Battery
# ============================================================
class Battery(db.Model):
    __tablename__ = "batteries"
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(80), default="LFP-72V-30Ah")
    capacity_kwh = db.Column(db.Float, default=3.0)
    soc = db.Column(db.Float, default=100.0)              # State of Charge
    soh = db.Column(db.Float, default=100.0)              # State of Health
    cycle_count = db.Column(db.Integer, default=0)
    temperature_c = db.Column(db.Float, default=25.0)
    current_station_id = db.Column(db.Integer, db.ForeignKey("swap_stations.id"), nullable=True)
    status = db.Column(db.String(20), default="ready")   # ready, charging, fault, in_use
    last_charged_at = db.Column(db.DateTime, default=datetime.utcnow)
    manufactured_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship("MaintenanceTicket", backref="battery", lazy=True)
    # NOTE: رابطه swap_events به‌دلیل وجود دو ForeignKey (old_battery_id و new_battery_id)
    # در SwapEvent ایجاد ابهام می‌کرد. به‌جای آن از روابط old_battery / new_battery
    # که در خود SwapEvent با foreign_keys صریح تعریف شده‌اند استفاده می‌شود.

    def is_healthy(self):
        return self.soh >= 70 and self.status != "fault" and self.cycle_count < 1500

    def predicted_failure_risk(self):
        """ریسک خرابی 0..1 بر اساس soh, cycle, temp"""
        risk = 0.0
        if self.soh < 80:
            risk += (80 - self.soh) / 80 * 0.5
        if self.cycle_count > 800:
            risk += min(1.0, (self.cycle_count - 800) / 700) * 0.3
        if self.temperature_c > 45:
            risk += min(1.0, (self.temperature_c - 45) / 20) * 0.2
        return round(min(1.0, risk), 3)

    def to_dict(self):
        return {
            "id": self.id,
            "serial": self.serial,
            "model": self.model,
            "capacity_kwh": self.capacity_kwh,
            "soc": self.soc,
            "soh": self.soh,
            "cycle_count": self.cycle_count,
            "temperature_c": self.temperature_c,
            "current_station_id": self.current_station_id,
            "status": self.status,
            "last_charged_at": self.last_charged_at.isoformat() if self.last_charged_at else None,
            "is_healthy": self.is_healthy(),
            "failure_risk": self.predicted_failure_risk(),
        }

# ============================================================
# Vehicle
# ============================================================
class Vehicle(db.Model):
    __tablename__ = "vehicles"
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(30), unique=True, nullable=False)
    model = db.Column(db.String(80), default="MAPNA E-Motor 125")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    battery_id = db.Column(db.Integer, db.ForeignKey("batteries.id"), nullable=True)
    odometer_km = db.Column(db.Float, default=0.0)
    last_service_km = db.Column(db.Float, default=0.0)
    service_interval_km = db.Column(db.Float, default=5000.0)
    status = db.Column(db.String(20), default="ready")  # ready, in_service, maintenance, fault
    in_pilot = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship("Trip", backref="vehicle", lazy=True)
    battery = db.relationship("Battery", foreign_keys=[battery_id])

    def km_to_next_service(self):
        return max(0.0, self.service_interval_km - (self.odometer_km - self.last_service_km))

    def service_due_soon(self):
        return self.km_to_next_service() < 500

    def to_dict(self):
        return {
            "id": self.id,
            "plate": self.plate,
            "model": self.model,
            "owner_id": self.owner_id,
            "company_id": self.company_id,
            "battery_id": self.battery_id,
            "odometer_km": self.odometer_km,
            "status": self.status,
            "in_pilot": self.in_pilot,
            "km_to_next_service": self.km_to_next_service(),
            "service_due_soon": self.service_due_soon(),
        }# ============================================================
# Trip
# ============================================================
class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    start_lat = db.Column(db.Float, nullable=False)
    start_lng = db.Column(db.Float, nullable=False)
    end_lat = db.Column(db.Float)
    end_lng = db.Column(db.Float)
    distance_km = db.Column(db.Float, default=0.0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    energy_kwh = db.Column(db.Float, default=0.0)
    co2_saved_kg = db.Column(db.Float, default=0.0)
    cost_toman = db.Column(db.Float, default=0.0)
    weather = db.Column(db.String(40), default="clear")

    def to_dict(self):
        return {
            "id": self.id,
            "rider_id": self.rider_id,
            "vehicle_id": self.vehicle_id,
            "start_lat": self.start_lat,
            "start_lng": self.start_lng,
            "end_lat": self.end_lat,
            "end_lng": self.end_lng,
            "distance_km": self.distance_km,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "energy_kwh": self.energy_kwh,
            "co2_saved_kg": self.co2_saved_kg,
            "cost_toman": self.cost_toman,
            "weather": self.weather,
        }

# ============================================================
# PriceRule (قیمت‌گذاری پویا)
# ============================================================
class PriceRule(db.Model):
    __tablename__ = "price_rules"
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey("swap_stations.id"), nullable=False)
    hour_start = db.Column(db.Integer, default=0)   # 0..23
    hour_end = db.Column(db.Integer, default=23)
    weekday_mask = db.Column(db.String(20), default="1,1,1,1,1,1,1")  # Mon..Sun
    demand_factor = db.Column(db.Float, default=1.0)        # ضریب بر اساس تقاضا
    multiplier = db.Column(db.Float, default=1.0)
    priority = db.Column(db.Integer, default=0)

    def matches(self, weekday, hour):
        wd = (weekday + 6) % 7  # Mon=0
        try:
            mask = [int(x) for x in self.weekday_mask.split(",")]
        except Exception:
            mask = [1] * 7
        if wd < 0 or wd >= 7 or mask[wd] == 0:
            return False
        if self.hour_start <= self.hour_end:
            return self.hour_start <= hour <= self.hour_end
        return hour >= self.hour_start or hour <= self.hour_end

    def to_dict(self):
        return {
            "id": self.id,
            "station_id": self.station_id,
            "hour_start": self.hour_start,
            "hour_end": self.hour_end,
            "weekday_mask": self.weekday_mask,
            "demand_factor": self.demand_factor,
            "multiplier": self.multiplier,
            "priority": self.priority,
        }

# ============================================================
# SwapEvent (رویداد تعویض)
# ============================================================
class SwapEvent(db.Model):
    __tablename__ = "swap_events"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"))
    station_id = db.Column(db.Integer, db.ForeignKey("swap_stations.id"), nullable=False)
    old_battery_id = db.Column(db.Integer, db.ForeignKey("batteries.id"))
    new_battery_id = db.Column(db.Integer, db.ForeignKey("batteries.id"))
    energy_kwh = db.Column(db.Float, default=3.0)
    price_toman = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="completed")  # reserved, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    co2_saved_kg = db.Column(db.Float, default=0.0)

    old_battery = db.relationship("Battery", foreign_keys=[old_battery_id])
    new_battery = db.relationship("Battery", foreign_keys=[new_battery_id])
    vehicle = db.relationship("Vehicle", foreign_keys=[vehicle_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
            "station_id": self.station_id,
            "old_battery_id": self.old_battery_id,
            "new_battery_id": self.new_battery_id,
            "energy_kwh": self.energy_kwh,
            "price_toman": self.price_toman,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "co2_saved_kg": self.co2_saved_kg,
        }

# ============================================================
# MaintenanceTicket
# ============================================================
class MaintenanceTicket(db.Model):
    __tablename__ = "maintenance_tickets"
    id = db.Column(db.Integer, primary_key=True)
    battery_id = db.Column(db.Integer, db.ForeignKey("batteries.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"))
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default="low")  # low, medium, high, critical
    status = db.Column(db.String(20), default="open")  # open, in_progress, resolved
    predicted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "battery_id": self.battery_id,
            "vehicle_id": self.vehicle_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "predicted": self.predicted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

# ============================================================
# ChatMessage (تاریخچه چت با AI)
# ============================================================
class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), default="user")
    content = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }