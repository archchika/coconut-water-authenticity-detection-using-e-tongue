# Security and Environment Template (Phase 6.8)

Checklist for HTTPS, CORS, secure cookies, rate limiting, and environment configuration. **No secrets in the repository.**

---

## 1. HTTPS

- Serve the Django API and React app over **HTTPS only** in production.
- Backend: `SECURE_SSL_REDIRECT = True` in production settings (or set via env `SECURE_SSL_REDIRECT=true`) so HTTP is redirected to HTTPS. Disable if the reverse proxy (e.g. Nginx, load balancer) already forces HTTPS.
- Frontend: Deploy on a host that provides TLS (Vercel, Netlify, etc.).

---

## 2. CORS

- **Development:** `CORS_ALLOW_ALL_ORIGINS = True` (base settings) for local frontend (e.g. `localhost:5173`).
- **Production:** `CORS_ALLOW_ALL_ORIGINS = False`; set `CORS_ALLOWED_ORIGINS` to the exact frontend origin(s), e.g. `https://www.example.com,https://admin.example.com`. No wildcards; comma-separated list from env.

---

## 3. Secure cookies

In production settings (`config.settings.production`):

- `SESSION_COOKIE_SECURE = True` — session cookie only over HTTPS.
- `CSRF_COOKIE_SECURE = True` — CSRF cookie only over HTTPS.
- `SECURE_BROWSER_XSS_FILTER = True`, `SECURE_CONTENT_TYPE_NOSNIFF = True` — security headers.

---

## 4. Rate limiting

- **Upload endpoint** `POST /api/upload-data/` is throttled per authenticated user (Phase 6.8).
- Throttle scope: `upload`. Default rate in production: **60/hour** (configurable via env `UPLOAD_THROTTLE_RATE`, e.g. `120/hour`).
- Implemented with DRF `UserRateThrottle` and custom `UploadRateThrottle`; rate defined in `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["upload"]`.

---

## 5. Environment template and no secrets in repo

- **Backend:** Copy `backend/.env.example` to `backend/.env` (or set env vars in the host). Fill in real values for `SECRET_KEY`, `DB_*`, `CORS_ALLOWED_ORIGINS`, etc. **Do not commit `.env` or any file containing secrets.**
- **Frontend:** Copy `frontend/.env.example` to `frontend/.env.local` if needed; only `VITE_*` vars are exposed to the client. No API keys or secrets in frontend env that are sensitive.
- **Repository:** No `SECRET_KEY`, passwords, API keys, or tokens in the repo. Use env vars or a secrets manager in production.

See **docs/DEPLOYMENT.md** for the full list of backend and frontend env vars.
