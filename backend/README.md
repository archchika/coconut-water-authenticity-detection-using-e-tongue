# Backend — Django API (Phase 5)

IoT cloud communication, REST API, PostgreSQL (Phase 5.4), auth, and admin.

## Phase 5.3 — Project and app structure (done)

- **Project layout**
  - **`config/`** — Django project: `settings/base.py`, `settings/production.py`, `urls.py`, `wsgi.py`, `asgi.py`.
  - **`api/`** — API package: URL routing under `/api/` (upload and aggregation in 5.5–5.6).
  - **`core/`** — Shared utilities and constants.
- **Apps**
  - **`readings`** — Sensor readings and predictions (models in 5.4).
  - **`alerts`** — Alerts (adulteration, sensor fault; models in 5.4).
  - **`logs`** — System operational logs (models in 5.4).
- **Settings**
  - **Base** (`config.settings` or `config.settings.base`): SQLite, DEBUG=True, CORS allow all, REST framework.
  - **Production** (`config.settings.production`): DEBUG=False, PostgreSQL from env, SECRET_KEY and ALLOWED_HOSTS from env.

### Run locally

```bash
cd backend
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings   # or leave default
python manage.py migrate
python manage.py runserver
```

**Windows (PowerShell):** If you see "running scripts is disabled", run once:  
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
Then: `.\\.venv\Scripts\Activate.ps1` and `python manage.py runserver`.  

**Windows (no activation):** Use the venv Python directly (no script policy needed):  
`.\\.venv\Scripts\python.exe manage.py runserver`  

Or run **`run.bat`** from the `backend` folder to start the server.

Admin: http://127.0.0.1:8000/admin/  
API: http://127.0.0.1:8000/api/ — **POST /api/upload-data/** (5.5, **auth required** in 5.7); **GET /api/daily/**, **/api/weekly/**, **/api/monthly/** (5.6, public); **POST /api/auth/token/** (5.7) to obtain a token.

### Phase 5.4 — PostgreSQL models and migrations (done)

- **readings**: `SensorReading` (timestamp, ph, tds, temperature, turbidity, source_device_id), `Prediction` (reading 1:1, predicted_sugar/citric/ascorbic, authenticity_status, confidence), `CalibrationData` (optional metadata).
- **alerts**: `Alert` (timestamp, type, message, reading FK nullable, resolved).
- **logs**: `SystemLog` (timestamp, level, component, message, metadata JSON).
- Indexes on timestamp and status fields for daily/weekly/monthly queries.
- Migrations: `readings/migrations/0001_initial.py`, `alerts/0001_initial.py`, `logs/0001_initial.py`. Run `python manage.py migrate`.
- Schema: **`backend/docs/database.md`**.

### Phase 5.5 — Serializers and upload API (done)

- **`readings/serializers.py`** — **UploadPayloadSerializer**: validates `timestamp`, `pH`, `tds`, `temperature`, `turbidity`, `predicted_sugar`, `predicted_citric`, `predicted_ascorbic`, `status` (authentic/adulterated); optional `confidence`, `source_device_id`. Accepts `ph` as alias for `pH`.
- **`readings/views.py`** — **UploadDataView**: POST creates `SensorReading` and `Prediction`; if `status=adulterated`, creates **Alert** (type=adulteration) and **SystemLog** (level=WARNING, component=upload).
- **URL:** **POST /api/upload-data/** → 201 with `reading_id`, `prediction_id`, `timestamp` or 400 with validation errors. **Requires authentication** (Phase 5.7).

### Phase 5.6 — Aggregation endpoints (done)

- **GET /api/daily/?date=YYYY-MM-DD** — Aggregated data for one day (UTC).
- **GET /api/weekly/?year=YYYY&week=W** — Aggregated data for ISO week (e.g. year=2025&week=8).
- **GET /api/monthly/?year=YYYY&month=M** — Aggregated data for calendar month (e.g. year=2025&month=2).
- Response: `period`, `period_type`, `count`, `averages` (ph, tds, temperature, turbidity, predicted_sugar, predicted_citric, predicted_ascorbic), `authenticity` (authentic count, adulterated count), `status` ("authentic" | "adulterated" for the period).
- **`readings/aggregation.py`** — `aggregate_daily`, `aggregate_weekly`, `aggregate_monthly`; **`readings/views.py`** — `DailyAggregationView`, `WeeklyAggregationView`, `MonthlyAggregationView`.

### Phase 5.7 — Authentication (done)

- **Token authentication** for upload and admin: `rest_framework.authtoken` in `INSTALLED_APPS`; `TokenAuthentication` and `SessionAuthentication` in `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`.
- **POST /api/upload-data/** requires **IsAuthenticated** (Token or Session). Send header: `Authorization: Token <your-token>`.
- **GET /api/daily/**, **/api/weekly/**, **/api/monthly/** are **AllowAny** (public read-only for dashboard).
- **POST /api/auth/token/** — obtain a token: send `username` and `password` in JSON body; returns `{"token": "..."}`. Use that token in `Authorization: Token <key>` for upload.
- **Getting a token:** Create a Django user (e.g. in admin), then create a Token for that user (Admin → Auth Token → Add, or run `python manage.py shell` and `Token.objects.get_or_create(user=user)`). Alternatively POST to `/api/auth/token/` with the user’s credentials. Run `python manage.py migrate` so the `authtoken_token` table exists.
- **Phase 6.5 — Admin list APIs (auth required):** **GET /api/readings/** — list SensorReadings with optional `date_from`, `date_to`, `limit` (default 50, max 500). **GET /api/predictions/** — list Predictions with optional `date_from`, `date_to`, `status` (authentic|adulterated), `limit`.
- **Phase 6.6 — Alerts and logs (auth required):** **GET /api/alerts/** — list Alerts with optional `date_from`, `date_to`, `type`, `resolved` (true|false), `limit`. **PATCH /api/alerts/<id>/** — body `{ "resolved": true|false }` to mark resolved/unresolved. **GET /api/logs/** — list SystemLogs with optional `date_from`, `date_to`, `level`, `component`, `search` (message), `limit`.

### Phase 5.8 — Admin panel and logging abnormal cases (done)

- **Admin:** All models (SensorReading, Prediction, CalibrationData, Alert, SystemLog) are registered with **filters** (date, status, type, resolved, level, component), **date_hierarchy**, **search_fields**, and **list_per_page = 50**. **Alert** has actions: **Mark as resolved** / **Mark as unresolved**.
- **On upload:** If **status = adulterated**, create **Alert** (type=adulteration) and **SystemLog** (WARNING, component=upload) — already in 5.5. If any **sensor value is out-of-range** (ph, tds, temperature, turbidity outside bounds in **`core/constants.SENSOR_RANGES`**), create **Alert** (type=out_of_range) and **SystemLog** (WARNING, sensor out-of-range). Bounds: ph 0–14, tds 0–20000, temperature -10–60, turbidity 0–500.

### Phase 5.9 — Schema documentation and env template (done)

- **docs/database.md:** Schema diagram (ASCII ER) added: SensorReading → Prediction (1:1), Alert → SensorReading (optional FK), SystemLog and CalibrationData; tables and relationships.
- **.env.example:** Template for production env vars: `SECRET_KEY`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, optional `CORS_ALLOWED_ORIGINS`, `STATIC_ROOT`, and `DATABASE_URL` (alternative to DB_*). Copy to `.env` and fill in; do not commit `.env`.

### Phase 6.7 — Deployment architecture (done)

- **docs/DEPLOYMENT.md** (at repo root): factory (offline) vs cloud; Django/PostgreSQL/React hosting; env vars; production settings; security.

### Phase 6.8 — Security and environment template (done)

- **HTTPS / secure cookies:** In production: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`.
- **CORS:** Whitelist via `CORS_ALLOWED_ORIGINS` (production); no wildcards.
- **Rate limiting:** `POST /api/upload-data/` throttled per user (scope `upload`, default 60/hour); set `UPLOAD_THROTTLE_RATE` in env to override. **UploadDataView** uses **UploadRateThrottle** and **IsAuthenticated**.
- **.env.example:** Updated with `SECURE_SSL_REDIRECT`, `UPLOAD_THROTTLE_RATE`; no secrets in repo. **docs/SECURITY.md** at repo root for full checklist.

### Phase 6.9 — Full data flow diagram (done)

- **docs/DATA_FLOW.md** (at repo root): ASCII diagram Sensors → ESP32 → Fusion → ML → Local UI → Cloud API → DB → React (public + admin); stage table.

### Phase 6.10 — Research documentation (IEEE style) (done)

- **docs/research/METHODOLOGY.md:** Methodology (E-Tongue setup, sensor choice, calibration protocol); calibration modelling table (reference points); mathematical formulation (feature vector, regression, authenticity ranges \(L_k, U_k\)); innovation justification and industrial impact; references placeholder.
