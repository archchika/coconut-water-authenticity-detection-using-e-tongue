# Deployment Architecture (Phase 6.7)

This document describes the deployment design for the Ceylon Coco E-Tongue system: **factory (offline)** vs **cloud**, environment variables, and production settings.

---

## 1. Overview: Factory vs Cloud

| Layer | Factory (offline) | Cloud |
|-------|-------------------|--------|
| **Role** | Real-time sensing, fusion, ML inference, local UI, optional cleaning automation | Ingest uploaded data, store in DB, serve public and admin dashboards |
| **Connectivity** | No cloud required for detection; upload when online | Always on; receives HTTP POST from devices and serves React frontends |
| **Components** | ESP32, Raspberry Pi (or local PC), sensor fusion (Phase 2), ML inference (Phase 3), Streamlit (Phase 4) | Django API, PostgreSQL, React (public + admin) |

---

## 2. Factory (Offline) Layer

- **ESP32:** Reads sensors (pH, TDS, temperature, turbidity); 3× average; threshold check; buzzer on alert; sends over Serial or WiFi.
- **Raspberry Pi / Local PC:** Receives data; runs **sensor fusion** (Phase 2: filter, moving average, baseline norm) → feature vector.
- **ML inference (Phase 3):** Load trained model; predict sugar, citric, ascorbic; range check → **Authentic / Adulterated**.
- **Local Streamlit dashboard (Phase 4):** Real-time graphs, alert box, state, mini log. No cloud required for detection.
- **Cleaning automation (optional):** Arm → rinse → dry → stabilise → READY.
- **When online:** HTTP POST to cloud **Django API** (`/api/upload-data/`) with token auth; payload includes timestamp, sensor values, predictions, status.

---

## 3. Cloud Layer

- **Django backend:** REST API (upload, daily/weekly/monthly aggregation, admin list endpoints). Deploy on **AWS**, **Railway**, **Render**, or similar. Use **gunicorn** (or uWSGI) behind a reverse proxy (e.g. Nginx, or provider’s proxy).
- **PostgreSQL:** Managed database (e.g. AWS RDS, Railway Postgres, Render PostgreSQL). Stores SensorReadings, Predictions, Alerts, SystemLogs, CalibrationData.
- **React frontend:** Public transparency dashboard + admin dashboard. Deploy on **Vercel**, Netlify, or same host as API. Set **VITE_API_BASE_URL** to the Django API origin in production.

---

## 4. Environment Variables

All secrets and config must come from **environment variables**; **no secrets in the repository**.

### Backend (Django)

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret; **required** in production |
| `ALLOWED_HOSTS` | Comma-separated hosts (e.g. `api.example.com`) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection (or use `DATABASE_URL`) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins for the React app (e.g. `https://www.example.com`) |
| `STATIC_ROOT` | Directory for `collectstatic` (e.g. `/var/www/backend/staticfiles`) |
| `DJANGO_SETTINGS_MODULE` | Set to `config.settings.production` in production |

See **`backend/.env.example`** for a template. Copy to `.env` (or set in the host’s env) and never commit `.env`.

### Frontend (React)

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Django API base URL (no trailing slash), e.g. `https://api.example.com`. Omit in dev to use Vite proxy. |

See **`frontend/.env.example`**.

---

## 5. Production Settings (Django)

- **DEBUG:** `False`.
- **HTTPS:** Serve the API over HTTPS only (reverse proxy or provider TLS).
- **CORS:** `CORS_ALLOW_ALL_ORIGINS = False`; set `CORS_ALLOWED_ORIGINS` to the frontend origin(s).
- **Secure cookies:** Use provider defaults or set cookie flags (e.g. `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) when using session auth.
- **Rate limiting:** Apply rate limiting on the upload endpoint (`/api/upload-data/`) to avoid abuse (e.g. django-ratelimit or reverse-proxy limits).
- **Static files:** Run `python manage.py collectstatic`; serve via reverse proxy or CDN from `STATIC_ROOT`.

---

## 6. Security Summary

- **HTTPS only** for API and frontend.
- **Authentication:** Token (or JWT) for upload and admin; public read-only endpoints (daily/weekly/monthly) can remain unauthenticated or use an optional API key.
- **Input validation and sanitisation:** Serializers validate upload payload; restrict allowed hosts and CORS.
- **Optional:** API key or dedicated token for device upload (same as current token auth).
- **Secrets:** Only in env; **no secrets in repo** or client bundles.
- **Rate limiting:** Upload endpoint throttled per user (e.g. 60/hour); see **docs/SECURITY.md** and backend `.env.example` (`UPLOAD_THROTTLE_RATE`).
- **Secure cookies and CORS:** See **docs/SECURITY.md** for checklist (HTTPS, CORS whitelist, secure cookies).

---

## 7. Suggested Hosting Combinations

- **Backend:** Railway, Render, or AWS (EC2/ECS + RDS).
- **Database:** Managed PostgreSQL from the same provider or AWS RDS.
- **Frontend:** Vercel or Netlify (build from `frontend/` with `VITE_API_BASE_URL` set in project env).

After deployment, point the React app at the API URL and configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` accordingly.
