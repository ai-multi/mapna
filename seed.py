# seed.py
"""پر کردن دیتابیس با داده‌های نمونه برای دمو"""
from datetime import datetime, timedelta
import random

from app import create_app
from models import (
    db, Company, User, SwapStation, StationSlot, Battery,
    Vehicle, Trip, SwapEvent, PriceRule, MaintenanceTicket
)

def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---------------- Companies ----------------
        mapna = Company(name="MAPNA Logistics", tax_id="10101010", contact_phone="021-88776655")
        snapp = Company(name="Snapp E-Ride", tax_id="20202020", contact_phone="021-44556677")
        tapas = Company(name="Tapas Delivery", tax_id="30303030", contact_phone="021-22334455")
        db.session.add_all([mapna, snapp, tapas])
        db.session.commit()

        # ---------------- Stations (تهران) ----------------
        stations_data = [
            {"name": "ایستگاه آزادی",   "address": "میدان آزادی",     "lat": 35.6997, "lng": 51.3380},
            {"name": "ایستگاه ونک",     "address": "میدان ونک",       "lat": 35.7589, "lng": 51.4159},
            {"name": "ایستگاه تجریش",   "address": "تجریش",           "lat": 35.8028, "lng": 51.4267},
            {"name": "ایستگاه جمهوری",  "address": "میدان جمهوری",    "lat": 35.6960, "lng": 51.3890},
            {"name": "ایستگاه رسالت",   "address": "خیابان رسالت",    "lat": 35.7325, "lng": 51.4530},
            {"name": "ایستگاه مدرس",    "address": "خیابان مدرس",     "lat": 35.7420, "lng": 51.4200},
            {"name": "ایستگاه ستاری",   "address": "ستاری",           "lat": 35.7600, "lng": 51.3500},
        ]
        stations = []
        for sd in stations_data:
            s = SwapStation(
                name=sd["name"], address=sd["address"],
                lat=sd["lat"], lng=sd["lng"],
                capacity_slots=24, available_slots=24,
                fast_charge_kw=22.0, is_active=True,
                opening_hour=6, closing_hour=23,
            )
            db.session.add(s)
            stations.append(s)
        db.session.commit()# ---------------- Users ----------------
        admin = User(email="admin@swapfleet.ir", full_name="مدیر کل سیستم", role="admin", phone="021-11111111")
        admin.set_password("admin123")
        station_user = User(email="station@swapfleet.ir", full_name="مدیر ایستگاه ونک", role="station", phone="021-22222222", home_station_id=stations[1].id)
        station_user.set_password("station123")
        fleet_user = User(email="fleet@swapfleet.ir", full_name="مدیر ناوگان MAPNA", role="fleet", phone="021-33333333", company_id=mapna.id)
        fleet_user.set_password("fleet123")
        rider_user = User(email="rider@swapfleet.ir", full_name="علی محمدی", role="rider", phone="09121111111", home_station_id=stations[0].id)
        rider_user.set_password("rider123")

        db.session.add_all([admin, station_user, fleet_user, rider_user])
        db.session.commit()

        stations[1].manager_id = station_user.id
        db.session.commit()

        # ---------------- Batteries ----------------
        random.seed(42)
        batteries = []
        for i in range(80):
            b = Battery(
                serial=f"BAT-{1000+i:05d}",
                model=random.choice(["LFP-72V-30Ah", "NMC-72V-40Ah"]),
                capacity_kwh=random.choice([3.0, 3.5, 4.0]),
                soc=random.randint(15, 100),
                soh=random.randint(60, 100),
                cycle_count=random.randint(50, 1400),
                temperature_c=random.randint(20, 55),
                current_station_id=random.choice(stations).id,
                status=random.choice(["ready", "ready", "ready", "charging", "fault"]),
            )
            db.session.add(b)
            batteries.append(b)
        db.session.commit()

        # ساخت اسلات برای هر ایستگاه
        for s in stations:
            for i in range(s.capacity_slots):
                slot = StationSlot(
                    station_id=s.id, slot_code=f"S{i+1:02d}", status="empty"
                )
                db.session.add(slot)
        db.session.commit()

        # تخصیص باتری‌های ready به اسلات‌ها
        for st in stations:
            ready_bats = [b for b in batteries if b.current_station_id == st.id and b.status == "ready"][:st.capacity_slots]
            empty_slots = StationSlot.query.filter_by(station_id=st.id, status="empty").limit(len(ready_bats)).all()
            for b, sl in zip(ready_bats, empty_slots):
                sl.battery_id = b.id
                sl.status = "ready"
            st.available_slots = max(0, st.capacity_slots - len(empty_slots))
        db.session.commit()# ---------------- Vehicles ----------------
        vehicles = []
        riders_for_vehicles = [
            ("علی احمدی", "09120000001"),
            ("حسین رضایی", "09120000002"),
            ("محمد کریمی", "09120000003"),
            ("فاطمه مرادی", "09120000004"),
            ("زهرا قاسمی", "09120000005"),
            ("رضا نوری", "09120000006"),
            ("نگار حسینی", "09120000007"),
            ("امیر صادقی", "09120000008"),
        ]
        rider_objs = []
        for name, phone in riders_for_vehicles:
            u = User(
                email=f"rider_{random.randint(10000,99999)}@swapfleet.ir",
                full_name=name, role="rider", phone=phone,
                company_id=mapna.id, home_station_id=random.choice(stations).id,
            )
            u.set_password("rider123")
            db.session.add(u)
            rider_objs.append(u)
        db.session.commit()

        for i, r in enumerate(rider_objs):
            v = Vehicle(
                plate=f"{random.randint(10,99)}ا{random.randint(100,999)}-ایران-{random.randint(10,99)}",
                model=random.choice(["MAPNA E-Motor 125", "MAPNA E-Motor 150"]),
                owner_id=r.id,
                company_id=mapna.id,
                battery_id=random.choice(batteries).id,
                odometer_km=random.randint(500, 18000),
                last_service_km=random.randint(0, 3000),
                service_interval_km=5000.0,
                status=random.choice(["ready", "ready", "ready", "in_service", "maintenance"]),
                in_pilot=True,
            )
            db.session.add(v)
            vehicles.append(v)
        db.session.commit()

        # اضافه کردن یک وسیله برای rider اصلی
        main_vehicle = Vehicle(
            plate="12ب345-ایران-12",
            model="MAPNA E-Motor 150",
            owner_id=rider_user.id,
            company_id=mapna.id,
            battery_id=batteries[0].id,
            odometer_km=2300.0,
            last_service_km=0.0,
            status="ready",
            in_pilot=True,
        )
        db.session.add(main_vehicle)
        db.session.commit()

        # ---------------- Price Rules ----------------
        for s in stations:
            # ساعت اوج (17-22) ضریب 1.3
            db.session.add(PriceRule(
                station_id=s.id, hour_start=17, hour_end=22,
                weekday_mask="1,1,1,1,1,1,1", multiplier=1.3, priority=2,
            ))
            # آخر هفته
            db.session.add(PriceRule(
                station_id=s.id, hour_start=10, hour_end=20,
                weekday_mask="1,1,1,1,1,1,1", multiplier=1.1, priority=1,
            ))
        db.session.commit()# ---------------- Trips & Swaps ----------------
        now = datetime.utcnow()
        weather_options = ["clear", "rain", "wind", "hot", "cold"]

        for r in rider_objs + [rider_user]:
            for _ in range(random.randint(5, 12)):
                start = now - timedelta(days=random.randint(0, 25), hours=random.randint(0, 23))
                dist = round(random.uniform(2, 18), 2)
                energy = round(dist * 0.030 * random.uniform(1.0, 1.25), 3)
                cost = int(energy * 8500 * random.uniform(0.9, 1.3))
                co2 = round(energy * 0.55, 3)
                start_st = random.choice(stations)
                end_lat = start_st.lat + random.uniform(-0.05, 0.05)
                end_lng = start_st.lng + random.uniform(-0.05, 0.05)

                trip = Trip(
                    rider_id=r.id,
                    vehicle_id=main_vehicle.id if r.id == rider_user.id else random.choice(vehicles).id,
                    start_lat=start_st.lat, start_lng=start_st.lng,
                    end_lat=end_lat, end_lng=end_lng,
                    distance_km=dist,
                    started_at=start,
                    ended_at=start + timedelta(minutes=int(dist * 3)),
                    energy_kwh=energy,
                    co2_saved_kg=co2,
                    cost_toman=cost,
                    weather=random.choice(weather_options),
                )
                db.session.add(trip)
        db.session.commit()

        # ---------------- Swap Events ----------------
        for _ in range(40):
            st = random.choice(stations)
            ready_bat = next((b for b in batteries if b.current_station_id == st.id and b.status == "ready"), None)
            if not ready_bat:
                continue
            old_bat = random.choice(batteries)
            energy = ready_bat.capacity_kwh
            cost = int(energy * 8500 * random.uniform(0.9, 1.4))
            db.session.add(SwapEvent(
                user_id=random.choice(rider_objs + [rider_user]).id,
                vehicle_id=random.choice(vehicles).id,
                station_id=st.id,
                old_battery_id=old_bat.id,
                new_battery_id=ready_bat.id,
                energy_kwh=energy,
                price_toman=cost,
                status="completed",
                created_at=now - timedelta(days=random.randint(0, 25), hours=random.randint(0, 23)),
                co2_saved_kg=round(energy * 0.55, 3),
            ))
        db.session.commit()

        # ---------------- Maintenance Tickets ----------------
        db.session.add(MaintenanceTicket(
            battery_id=batteries[0].id, title="SoH پایین", severity="high", status="open",
            description="SoH به 68% کاهش یافته است", predicted=False,
        ))
        db.session.add(MaintenanceTicket(
            battery_id=batteries[2].id, title="دمای بالا", severity="critical", status="in_progress",
            description="دمای باتری به 55°C رسیده است", predicted=True,
        ))
        db.session.add(MaintenanceTicket(
            vehicle_id=vehicles[0].id, title="سرویس دوره‌ای نزدیک", severity="medium", status="open",
            description="کمتر از 300 کیلومتر تا سرویس", predicted=True,
        ))
        db.session.commit()

        print("✅ Seed completed:")
        print(f"   Stations: {SwapStation.query.count()}")
        print(f"   Users: {User.query.count()}")
        print(f"   Batteries: {Battery.query.count()}")
        print(f"   Vehicles: {Vehicle.query.count()}")
        print(f"   Trips: {Trip.query.count()}")
        print(f"   Swaps: {SwapEvent.query.count()}")
        print(f"   Tickets: {MaintenanceTicket.query.count()}")
        print()
        print("🔑 Demo accounts (email / password):")
        print("   admin@swapfleet.ir / admin123")
        print("   station@swapfleet.ir / station123")
        print("   fleet@swapfleet.ir / fleet123")
        print("   rider@swapfleet.ir / rider123")

if __name__ == "__main__":
    seed()