**Niha** 📧 [niharuksar2002@gmail.com] · 🔗 <a href="https://www.linkedin.com/in/niha-ruksar/"> LinkedIn </a> 
# 🎓 HabotConnect LSA Booking API

> A production-style backend that connects parents with Learning Support Assistants (LSAs) for children with learning difficulties — built as a hiring simulation for HabotConnect FZCO, and then pushed a bit further than asked.

[![Tests](https://img.shields.io/badge/tests-9%2F9%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django)]()
[![DRF](https://img.shields.io/badge/DRF-3.x-red)]()
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)]()


---

## 💡 Why this project exists

HabotConnect needed proof that a candidate could think like a backend engineer on day one — not just write code that runs, but design a system that protects itself from mistakes. This repo simulates the most demanding day on the job: a booking module that has to be **correct, fast, and honest about its own failures**.


---
## 🌟 What I added beyond the brief

The spec asked for a working booking module. I built one that a teammate could pick up on day one without asking me a single question — live API docs instead of static descriptions, an admin panel to actually see the data, a seeder so no one has to hand-craft test records, structured logging, and validation that catches bad input before it becomes a bad row in the database.

That's the standard I held this project to, and it's the standard I'd hold my work to on the team.

---

## ✨ What's inside
Every design choice below was made with one question in mind: *if this shipped to production tomorrow, would it hold up?*

| Capability | Where |
|---|---|
| 🧩 Normalized, indexed relational schema (Parent, LSA, Booking) | `bookings/models.py` |
| 🚫 Double-booking prevention — enforced at both app and DB level | `models.py` + `serializers.py` |
| ⚡ N+1-safe LSA search endpoint | `views.py` |
| 💳 Payment webhook with a real state machine (`PENDING → CONFIRMED / FAILED`) | `views.py` + `services.py` |
| ✅ 9 automated tests — success, edge, and failure paths | `test_views.py` |
| 🔄 CI pipeline that runs the full suite on every push | `.github/workflows/test.yml` |
| 📖 Live, interactive API docs (Swagger/OpenAPI) | `/api/docs/` |
| 🛠 Admin panel wired to all three models | `/admin/` |
| 🌱 One-command demo data seeder | `manage.py seed_demo_data` |
| ☎️ International phone number validation (E.164) | `models.py` |
| 🧯 Consistent, predictable API error shape | `bookings/exceptions.py` |
| 🏠 A real root endpoint (not a 404) | `/` |

---

## 🏗 Architecture

```
Client
  │
  ▼
Django REST Views  ──▶  Serializers (validation)  ──▶  Models (schema rules)
  │                                                         │
  ▼                                                         ▼
Mock Payment Gateway                                    Database
(webhook only)
```

**Project layout:**

```
habotconnect-booking-api/
├── habotconnect/          # Django project — settings, root URLs
└── bookings/               # Django app — the actual feature
    ├── models.py            # Parent, LSAProfile, BookingRequest
    ├── serializers.py        # Validation + double-booking guard
    ├── views.py               # Home, Booking, Search, Webhook
    ├── services.py             # Mock payment gateway integration
    ├── exceptions.py            # Consistent error responses
    ├── admin.py                  # Admin panel registration
    ├── test_views.py               # 9 tests
    └── management/commands/
        └── seed_demo_data.py       # Demo data in one command
```

---

## 🧠 The three decisions worth knowing about

**1. Double bookings are impossible, not just discouraged.**
An LSA's schedule is protected two ways: a Django-level overlap check (`new.start < existing.end AND new.end > existing.start`) *and* a database `CheckConstraint` guaranteeing `session_end > session_start`. Even a raw SQL insert or a careless admin edit can't corrupt a booking.

**2. The LSA search endpoint doesn't do N+1 queries.**
Fetching 50 LSAs shouldn't mean 51 database round-trips. `prefetch_related("bookings")` collapses what would be N+1 queries into 2, flat, regardless of result size.

**3. The payment webhook models reality, not a shortcut.**
Bookings don't confirm themselves — they wait in `PENDING` until an external event (a mock payment gateway callback) tells them to become `CONFIRMED` or `FAILED`. This is how Stripe, Razorpay, and every real payment integration actually works.

---
## 🏛 Why MVT (Django), not MVC

Django follows **MVT (Model-View-Template)**, a variant of the classic **MVC (Model-View-Controller)** pattern:

| | MVC | MVT (Django) |
|---|---|---|
| Data + rules | Model | Model |
| Request handling | Controller | View |
| Presentation | View | Template |

The naming is the confusing part — Django's "View" plays the role MVC calls the "Controller" (it receives the request and decides what happens), while Django's "Template" plays the role MVC calls the "View" (the actual presentation layer). Django's framework itself acts as the traffic router that MVC leaves to the developer.

For this API, there's no Template layer in the traditional sense — DRF serializers act as the presentation/formatting layer instead, turning Model instances into JSON. So the practical mapping here is: **Model → schema, View → request logic + validation trigger, Serializer → the "shape" of what goes out.**
---

## 🚀 Quick start

```bash
git clone <this-repo-url>
cd habotconnect-booking-api
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data      # optional — populates sample data
python manage.py createsuperuser     # optional — for /admin/
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — API welcome page with links
- `http://127.0.0.1:8000/api/docs/` — interactive Swagger docs
- `http://127.0.0.1:8000/admin/` — browse seeded data

---

## 📡 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Service info + links |
| `POST` | `/api/v1/bookings/` | Create a booking (validates overlap) |
| `GET` | `/api/v1/lsas/search/?skill=` | Search active LSAs by skill |
| `POST` | `/api/payments/webhook/` | Payment gateway callback |
| `GET` | `/api/docs/` | Live Swagger UI |

Full request/response schemas are documented live at `/api/docs/` — not just described here, but actually testable.

---

## ✅ Running the tests

```bash
python -m pytest bookings/test_views.py -v
```

```
9 passed
```

Covers: successful booking creation, overlap rejection, invalid time ranges, skill-based search (including inactive-LSA exclusion), webhook success/failure transitions, unknown booking handling, and the root endpoint.

---

## 🔄 CI/CD

Every push runs the full test suite automatically via GitHub Actions — see `.github/workflows/test.yml`. No code reaches `main` without passing all 9 tests.

---


## 👩‍💻 Author

**Niha**
Backend Developer — Python | Django | FastAPI | REST APIs
📧 [niharuksar2002@gmail.com] · 🔗 <a href="https://www.linkedin.com/in/niha-ruksar/"> LinkedIn </a> · 🔗 <a href="https://niharuksar-portfolio.netlify.app/">Portfolio</a>
