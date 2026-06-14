# Runnable commands

Commands to run the **Ceylon Coco / E-Tongue** stack on **Windows PowerShell**.  
Project root: `C:\Users\archchika\Desktop\research`

---

## Run the system (minimum: 2 terminals)

| # | Component | URL | When |
|---|-----------|-----|------|
| **1** | Django backend | http://127.0.0.1:8000/ | Start **first** |
| **2** | React frontend | http://localhost:5173/ | Start after backend is up |

Optional third terminal: ML test (`run_predict.py`) or factory dashboard (`streamlit`).

---

## Terminal 1 — Django backend API

**Meaning:** REST API, admin panel, auth tokens, daily/weekly/monthly aggregation for the public and admin dashboards.

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

**Without activating venv** (if PowerShell blocks scripts):

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\.venv\Scripts\python.exe manage.py runserver
```

**Double-click alternative:** run `backend\run.bat` (uses venv Python, no activation).

---

## Terminal 2 — React frontend (Ceylon Coco)

**Meaning:** Public transparency dashboard + admin UI; dev server proxies `/api/*` → `http://127.0.0.1:8000`.

```powershell
cd C:\Users\archchika\Desktop\research\frontend
npm run dev
```

**First time only** (install dependencies):

```powershell
cd C:\Users\archchika\Desktop\research\frontend
npm install
npm run dev
```

**Double-click alternative:** run `frontend\run.bat`.

**Production build:**

```powershell
cd C:\Users\archchika\Desktop\research\frontend
npm run build
```

---

## Terminal 3 (optional) — ML prediction CLI

**Meaning:** Test `ML_1` Random Forest: pH + temperature → citric % and ascorbic % (no web server).

**Interactive:**

```powershell
cd C:\Users\archchika\Desktop\research\ML_1
python run_predict.py
```

**With arguments** (pH, then temperature °C):

```powershell
cd C:\Users\archchika\Desktop\research\ML_1
python run_predict.py 4.5 25
```

Example:

```
Enter pH: 4.5
Enter temperature (°C): 25
  Citric acid:   0.0005%
  Ascorbic acid: 0.0009%
```

---

## Terminal 3 (optional) — Local factory dashboard (Streamlit)

**Meaning:** Offline factory UI — live graphs, alerts, state (Phase 4). Needs a local data URL in `local_dashboard\config.yaml`.

```powershell
cd C:\Users\archchika\Desktop\research\local_dashboard
pip install -r requirements.txt
streamlit run app.py
```

Opens in the browser (default http://localhost:8501).

---

## First-time setup (run once)

### Backend — venv, packages, database

```powershell
cd C:\Users\archchika\Desktop\research\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
```

If `Activate.ps1` fails:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or skip activation and use `.\.venv\Scripts\python.exe` for all `manage.py` commands.

### Backend — admin user (for `/admin` and admin dashboard login)

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\.venv\Scripts\Activate.ps1
python manage.py createsuperuser
```

Then open http://127.0.0.1:8000/admin/ and sign in.

**API token** (for upload / admin API): Admin → **Auth Token** → add token for your user, or:

```powershell
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
user = get_user_model().objects.get(username="YOUR_USERNAME")
Token.objects.get_or_create(user=user)
```

### Backend — demo data for charts

**Meaning:** Fills DB with sample readings/predictions so public daily/weekly/monthly views are not empty.

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\.venv\Scripts\Activate.ps1
python manage.py load_sample_readings
```

Clear existing data and reload:

```powershell
python manage.py load_sample_readings --clear
```

### Frontend — Node dependencies

```powershell
cd C:\Users\archchika\Desktop\research\frontend
npm install
```

### ML_1 — Python dependencies

```powershell
cd C:\Users\archchika\Desktop\research
pip install -r ML_1/requirements.txt
```

---

## ML training (rebuild model, not needed every day)

Run from **project root**:

```powershell
cd C:\Users\archchika\Desktop\research
pip install -r ML_1/requirements.txt
python ML_1/merge_datasets.py
python ML_1/train_model.py
```

| Command | Meaning |
|---------|---------|
| `merge_datasets.py` | Merge citric + ascorbic CSVs → `ML_1/dataset/combined_pH_temp_600.csv` |
| `train_model.py` | Train Random Forest → `ML_1/models/random_forest_ph_temp.pkl` |

---

## Research / calibration tools (optional)

**Calibration curves (plots):**

```powershell
cd C:\Users\archchika\Desktop\research
pip install pandas matplotlib
python generate_calibration_curves.py
```

Output: `calibration_curves\*.png`

**Predict via interpolation** (not the RF model):

```powershell
cd C:\Users\archchika\Desktop\research
pip install pandas numpy scipy
python predict_from_calibration.py 4.5 25
```

---

## Full `ml/` module (4-sensor model, separate from `ML_1`)

**Meaning:** pH + TDS + turbidity + temperature → sugar, citric, ascorbic (older Phase 3 path).

```powershell
cd C:\Users\archchika\Desktop\research
pip install -r ml/requirements.txt
python ml/train_model.py
python ml/run_example_prediction.py
```

---

## Important URLs

| URL | Purpose |
|-----|---------|
| http://localhost:5173/ | Public dashboard |
| http://localhost:5173/admin | Admin dashboard (needs backend + login) |
| http://127.0.0.1:8000/admin/ | Django admin |
| http://127.0.0.1:8000/api/daily/?date=YYYY-MM-DD | Public daily aggregation |
| http://127.0.0.1:8000/api/auth/token/ | POST username/password → API token |

---

## Startup checklist

1. `migrate` + `load_sample_readings` (once, or when DB is empty)
2. **Terminal 1:** `runserver` — wait for `Starting development server`
3. **Terminal 2:** `npm run dev` — open http://localhost:5173/
4. (Optional) **Terminal 3:** `python run_predict.py` or `streamlit run app.py`

**Order matters:** backend before frontend.  
**Stop servers:** `Ctrl+C` in each terminal.
