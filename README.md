# ⚡ MAPNA SwapFleet AI

سیستم مدیریت هوشمند ناوگان سواپ باتری موتورسیکلت‌های برقی با تمرکز بر بهینه‌سازی مصرف انرژی و کاهش آلایندگی.

## 🏗️ معماری

| لایه | تکنولوژی |
|---|---|
| Backend | Flask + SQLAlchemy + SQLite |
| Frontend | HTML/CSS/JS خام + Leaflet |
| Authentication | JWT + bcrypt |
| AI Assistant | Rule-Based Mock + AVALAI |

## 👥 نقش‌های کاربری

| نقش | ایمیل | رمز |
|---|---|---|
| ادمین | admin@swapfleet.ir | admin123 |
| مدیر ایستگاه | station@swapfleet.ir | station123 |
| مدیر ناوگان | fleet@swapfleet.ir | fleet123 |
| موتورسوار | rider@swapfleet.ir | rider123 |

## 🚀 اجرا

```bash
pip install -r requirements.txt
python seed.py    # ساخت دیتابیس + داده نمونه
python app.py     # اجرا روی پورت 5000
```

سپس مرورگر را باز کنید: `http://localhost:5000`

## 📦 ماژول‌ها

- `models.py` — مدل‌های داده (Company, User, Vehicle, Battery, SwapStation, Trip, SwapEvent, MaintenanceTicket, ChatMessage, PriceRule)
- `auth.py` — JWT + role decorators
- `services/pricing.py` — قیمت‌گذاری پویا (ساعت، روز، تقاضا)
- `services/routing.py` — مسیریابی هوشمند با Haversine
- `services/predictions.py` — پیش‌بینی خرابی باتری و سرویس
- `services/analytics.py` — CO2، uptime، هزینه
- `services/llm_agent.py` — دستیار AI با 21 قابلیت

## 🤖 قابلیت‌های AI Assistant

ایستگاه، سلامت باتری، تاریخچه سفر، هزینه، سرویس، نکات اکو، مسیریابی، SOS، وضعیت شارژر، وضعیت ناوگان، پشتیبانی، در ماموریت، در سرویس، Downtime، Uptime، پایلوت، آماده سرویس، هشدارها، وضعیت موتور، SoC، میانگین SoC.

## 🔌 AVALAI

برای فعال‌سازی AVALAI، متغیر `AVALAI_API_KEY` را تنظیم کنید:

```bash
export AVALAI_API_KEY=your-key
```