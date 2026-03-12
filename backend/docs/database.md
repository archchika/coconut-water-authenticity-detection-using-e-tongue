# Database schema (Phase 5.4 / 5.9)

PostgreSQL (production) or SQLite (local). Models: SensorReadings, Predictions, Alerts, SystemLogs, CalibrationData.

## Schema diagram

```
                    ┌─────────────────────────────┐
                    │  readings_sensorreadings    │
                    │  (SensorReading)            │
                    ├─────────────────────────────┤
                    │ id (PK)                     │
                    │ timestamp                   │
                    │ ph, tds, temperature,       │
                    │ turbidity, source_device_id  │
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │ 1:1                    │                       │ 1:N (optional)
           ▼                        │                        ▼
┌─────────────────────────────┐    │         ┌─────────────────────────────┐
│  readings_predictions       │    │         │  alerts_alerts (Alert)       │
│  (Prediction)               │    │         ├─────────────────────────────┤
├─────────────────────────────┤    │         │ id (PK), timestamp, type,     │
│ id (PK), reading_id (FK 1:1)│    │         │ message, reading_id (FK),    │
│ timestamp, predicted_sugar,│    │         │ resolved                     │
│ predicted_citric,           │    │         └─────────────────────────────┘
│ predicted_ascorbic,         │    │
│ authenticity_status,        │    │         ┌─────────────────────────────┐
│ confidence                  │    │         │  logs_systemlogs (SystemLog)│
└─────────────────────────────┘    │         ├─────────────────────────────┤
                                   │         │ id (PK), timestamp, level,   │
                                   │         │ component, message, metadata │
                                   │         └─────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │  readings_calibrationdata   │
                    │  (CalibrationData)          │
                    ├────────────────────────────┤
                    │ id (PK), timestamp, run_id,│
                    │ metadata                   │
                    └────────────────────────────┘
```

## Tables

### readings_sensorreadings (SensorReading)

| Column            | Type        | Index | Description                    |
|-------------------|-------------|-------|--------------------------------|
| id                | bigint PK   | -     |                                |
| timestamp         | datetime    | ✓     | Reading time                   |
| ph                | float       | -     | pH                             |
| tds               | float       | -     | TDS                            |
| temperature       | float       | -     | Temperature                    |
| turbidity         | float       | -     | Turbidity                      |
| source_device_id  | varchar(64) | -     | Optional device id             |

### readings_predictions (Prediction)

| Column              | Type        | Index | Description                    |
|---------------------|-------------|-------|--------------------------------|
| id                  | bigint PK   | -     |                                |
| reading_id          | bigint FK   | -     | One-to-one → readings_sensorreadings |
| timestamp           | datetime    | ✓     | Prediction time                |
| predicted_sugar     | float       | -     | Sugar %                        |
| predicted_citric    | float       | -     | Citric acid %                  |
| predicted_ascorbic  | float       | -     | Ascorbic acid %                |
| authenticity_status | varchar(32) | ✓     | authentic / adulterated        |
| confidence          | float       | -     | Optional 0–1                   |

### alerts_alerts (Alert)

| Column     | Type         | Index | Description                    |
|------------|--------------|-------|--------------------------------|
| id         | bigint PK    | -     |                                |
| timestamp  | datetime     | ✓     | Auto on create                 |
| type       | varchar(64)  | ✓     | adulteration, sensor_fault, …  |
| message    | text         | -     |                                |
| reading_id | bigint FK    | -     | Nullable → readings_sensorreadings |
| resolved   | boolean      | ✓     | Default false                  |

### logs_systemlogs (SystemLog)

| Column    | Type        | Index | Description                    |
|-----------|-------------|-------|--------------------------------|
| id        | bigint PK   | -     |                                |
| timestamp | datetime    | ✓     | Auto on create                 |
| level     | varchar(16) | ✓     | INFO, WARNING, ERROR           |
| component | varchar(64) | -     |                                |
| message   | text        | -     |                                |
| metadata  | jsonb       | -     | Optional JSON                  |

### readings_calibrationdata (CalibrationData)

| Column    | Type        | Index | Description                    |
|-----------|-------------|-------|--------------------------------|
| id        | bigint PK   | -     |                                |
| timestamp | datetime    | ✓     | Auto on create                 |
| run_id    | varchar(64) | -     | Optional run id               |
| metadata  | jsonb       | -     | Baseline values, notes         |

## Relationships

- **Prediction** → **SensorReading** (OneToOne, CASCADE).
- **Alert** → **SensorReading** (ForeignKey, SET_NULL, optional).

## Migrations

From `backend/`:

```bash
python manage.py migrate
```

Create new migrations after model changes:

```bash
python manage.py makemigrations readings alerts logs
```
