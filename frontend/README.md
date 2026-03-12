# Ceylon Coco — React Frontend (Phase 6)

Public transparency dashboard and private admin dashboard for the E-Tongue coconut water authenticity project.

## Phase 6.1 — Frontend project and API client (done)

- **Stack:** Vite + React 18 + TypeScript. Routing with `react-router-dom` (public vs admin).
- **API client:** `src/api/client.ts` — axios instance for Django; `fetchDaily`, `fetchWeekly`, `fetchMonthly`; `setAuthToken()` for upload/admin. Base URL from `VITE_API_BASE_URL` (default: same origin; dev proxy to backend in `vite.config.ts`).
- **Charts:** Recharts (e.g. `BarChart` on public dashboard). Placeholder period selectors and “Load” to hit `/api/daily/`, `/api/weekly/`, `/api/monthly/`.
- **Routes:** `/` — public dashboard; `/admin` — admin dashboard (protection in 6.5/6.6).
- **Dependencies:** `react`, `react-dom`, `react-router-dom`, `axios`, `recharts`, `date-fns`.

### Run

```bash
cd frontend
npm install
npm run dev
```

Dev server: http://localhost:5173. API requests to `/api/*` are proxied to `http://localhost:8000` (start Django with `python manage.py runserver` in `backend/`).

**Windows — if `npm` is not recognized:** Node may not be on PATH in your terminal. Either open a **new** terminal (after Node was installed) or run **`run.bat`** from the `frontend` folder — it uses Node’s full path and does not rely on PATH.

### Build

```bash
npm run build
```

Output in `dist/`. For production, set `VITE_API_BASE_URL` to your Django API origin (e.g. `https://api.example.com`).

### Phase 6.2 — Public dashboard: period selection and data fetch (done)

- **Period selectors:** Date (daily), Year + Week (weekly), Year + Month (monthly); “Load” fetches from `/api/daily/`, `/api/weekly/`, `/api/monthly/`.
- **Data fetch:** Initial fetch on mount (today for daily); user can change period and click “Load” to refetch.
- **Loading:** “Loading…” shown while request is in progress.
- **Errors:** Error message in a highlighted block with a “Retry” button.
- **Empty state:** “No readings for this period” when the API returns zero readings.

### Phase 6.3 — Public dashboard: graphs and authenticity badge (done)

- **Final averaged charts:** One bar chart for the selected period showing pH, Sugar %, Citric %, Ascorbic % (from API averages). Each metric has a distinct colour; tooltip shows values to 2 decimal places. Section title: “Averaged readings (pH & predicted %)”.
- **Authenticity badge:** Prominent pill-style badge: **Authentic** (green background) or **Adulterated** (red background), with clear colour coding and capitalised label.

### Phase 6.4 — Public dashboard: ingredient transparency summary (done)

- **Summary text:** “Ingredient transparency” section with short copy: predictions from the E-Tongue (sugar, citric, ascorbic) within natural ranges, plus a **link to methodology**.
- **Methodology page:** Route `/methodology` with a short description of the E-Tongue, sensors, calibration, and authenticity classification; link back to dashboard.
- **Responsive layout:** Public dashboard uses flex-wrap for period controls and responsive styles; at &lt;640px controls stack vertically and layout padding is reduced. Summary and methodology content use readable line length (max-width).

### Phase 6.5 — Admin dashboard: raw data and predictions (done)

- **Protected route:** `/admin` requires login. **AuthProvider** stores token in localStorage; **AdminLayout** shows **AdminLoginForm** when not authenticated. Login calls **POST /api/auth/token/**; token is set on the API client and used for admin requests.
- **Raw data tables:** Admin dashboard shows **Sensor readings** and **Predictions** in tables with columns matching the API (id, timestamp, ph, tds, temperature, turbidity, device; id, reading, timestamp, sugar/citric/ascorbic %, status, confidence).
- **Filters:** Date from, Date to (optional), Status for predictions (All / Authentic / Adulterated). “Apply” refetches both lists from **GET /api/readings/** and **GET /api/predictions/** with query params. Log out button in the admin header.

### Phase 6.6 — Admin dashboard: alerts and system logs (done)

- **Alerts:** Table with ID, Timestamp, Type, Message, Reading, Resolved. Filters: Type (text), Resolved (All / No / Yes). **Resolve action:** “Mark resolved” / “Mark unresolved” per row (calls **PATCH /api/alerts/<id>/** with `{ resolved: true|false }`), then updates local state.
- **System logs:** Table with ID, Timestamp, Level, Component, Message, Metadata. Filters: Level (INFO / WARNING / ERROR), Component (text), Search (message text). “Load logs” fetches **GET /api/logs/** with query params. Level is colour-coded (ERROR red, WARNING amber).

### Phase 6.7 — Deployment architecture design (done)

- **docs/DEPLOYMENT.md** at repo root: factory (ESP32 + Pi, local ML, Streamlit) vs cloud (Django, PostgreSQL, React); env vars for backend and frontend; production settings (DEBUG=False, HTTPS, CORS, rate limiting); security summary; suggested hosting (Railway/Render/AWS, Vercel/Netlify).

### Phase 6.8 — Security and environment template (done)

- **docs/SECURITY.md:** Checklist for HTTPS, CORS, secure cookies, rate limiting; env template; **no secrets in repo**.
- **Backend:** Production settings (Phase 6.8) add secure cookies (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`), `SECURE_SSL_REDIRECT`, and rate limiting on `POST /api/upload-data/` (throttle scope `upload`, e.g. 60/hour; configurable via `UPLOAD_THROTTLE_RATE`). **backend/.env.example** updated with `SECURE_SSL_REDIRECT`, `UPLOAD_THROTTLE_RATE`; **frontend/.env.example** notes no secrets in repo.

### Phase 6.9 — Full data flow diagram (done)

- **docs/DATA_FLOW.md** at repo root: final text/ASCII diagram from sensors → ESP32 → fusion → ML → local Streamlit → HTTP POST → Django API → PostgreSQL → React (public and admin dashboards). Includes a short stage-by-stage table.

### Phase 6.10 — Research documentation (IEEE style) (done)

- **docs/research/METHODOLOGY.md:** IEEE-style outline with Abstract; I. Introduction; II. Methodology (E-Tongue setup, sensor choice, robotic integration, calibration protocol); III. Calibration modelling (controlled samples, table of reference points pH/TDS/T/turbidity → sugar/citric/ascorbic); IV. Mathematical formulation (feature vector, regression equations, authenticity condition \(L_k, U_k\)); V. Innovation justification and industrial impact; References. Placeholders and sample calibration table for real data.
