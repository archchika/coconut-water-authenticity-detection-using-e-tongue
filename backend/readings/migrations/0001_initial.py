# Generated for Phase 5.4 — SensorReading, Prediction, CalibrationData

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SensorReading",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(db_index=True)),
                ("ph", models.FloatField()),
                ("tds", models.FloatField()),
                ("temperature", models.FloatField()),
                ("turbidity", models.FloatField()),
                ("source_device_id", models.CharField(blank=True, max_length=64, null=True)),
            ],
            options={
                "db_table": "readings_sensorreadings",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="CalibrationData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("run_id", models.CharField(blank=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "readings_calibrationdata",
                "ordering": ["-timestamp"],
                "verbose_name_plural": "Calibration data",
            },
        ),
        migrations.CreateModel(
            name="Prediction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(db_index=True)),
                ("predicted_sugar", models.FloatField()),
                ("predicted_citric", models.FloatField()),
                ("predicted_ascorbic", models.FloatField()),
                ("authenticity_status", models.CharField(db_index=True, max_length=32)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("reading", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="prediction", to="readings.sensorreading")),
            ],
            options={
                "db_table": "readings_predictions",
                "ordering": ["-timestamp"],
            },
        ),
    ]
