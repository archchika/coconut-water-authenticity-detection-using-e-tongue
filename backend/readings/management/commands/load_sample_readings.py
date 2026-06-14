"""
Load sample sensor readings and predictions for demo/dashboard.
Creates readings for today, this week, and this month so public aggregation views show data.
"""
from datetime import timedelta, timezone

from django.core.management.base import BaseCommand
from django.utils import timezone as django_tz

from readings.models import SensorReading, Prediction
from alerts.models import Alert
from logs.models import SystemLog


# Sample rows: (ph, tds, temp, turbidity, sugar, citric, ascorbic, status)
# pH: 4.5-6.5 typical for coconut water; citric 0.04-0.15%; ascorbic 0.05-0.12%; sugar 2-7%
SAMPLE_ROWS = [
    (5.10, 420.0, 26.5, 1.1, 5.00, 0.13, 0.09, "authentic"),
    (5.40, 380.0, 25.8, 0.9, 4.50, 0.11, 0.07, "authentic"),
    (5.20, 450.0, 27.0, 1.2, 4.80, 0.12, 0.08, "authentic"),
    (5.35, 410.0, 26.0, 1.0, 4.65, 0.10, 0.06, "authentic"),
    (5.23, 430.0, 26.8, 1.1, 4.77, 0.12, 0.08, "authentic"),
    (4.85, 520.0, 25.0, 1.6, 6.50, 0.19, 0.14, "adulterated"),
    (5.55, 395.0, 26.2, 1.0, 4.20, 0.09, 0.05, "authentic"),
    (5.30, 440.0, 26.5, 1.2, 4.90, 0.12, 0.08, "authentic"),
    (5.18, 435.0, 26.1, 1.0, 4.85, 0.11, 0.07, "authentic"),
    (5.42, 398.0, 25.8, 0.95, 4.55, 0.10, 0.06, "authentic"),
    (5.08, 455.0, 27.2, 1.15, 4.92, 0.12, 0.08, "authentic"),
    (5.28, 418.0, 26.4, 1.05, 4.72, 0.11, 0.07, "authentic"),
    (5.15, 442.0, 26.0, 1.1, 4.88, 0.12, 0.08, "authentic"),
    (5.38, 405.0, 25.9, 0.98, 4.62, 0.10, 0.06, "authentic"),
    (5.22, 428.0, 26.6, 1.08, 4.78, 0.11, 0.07, "authentic"),
]


class Command(BaseCommand):
    help = "Load sample sensor readings and predictions (today, this week, this month)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all SensorReading/Prediction/Alert/SystemLog before loading (optional).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing readings, predictions, alerts, logs...")
            SystemLog.objects.all().delete()
            Alert.objects.all().delete()
            Prediction.objects.all().delete()
            SensorReading.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared."))

        now = django_tz.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        created = 0
        # All 15 readings on today, spaced by 30 min so they're visible when selecting today
        for i, (ph, tds, temp, turb, sugar, citric, ascorbic, status) in enumerate(SAMPLE_ROWS):
            ts = now - timedelta(minutes=i * 30)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            reading = SensorReading.objects.create(
                timestamp=ts,
                ph=ph,
                tds=tds,
                temperature=temp,
                turbidity=turb,
                source_device_id="sample-device",
            )
            Prediction.objects.create(
                reading=reading,
                timestamp=ts,
                predicted_sugar=sugar,
                predicted_citric=citric,
                predicted_ascorbic=ascorbic,
                authenticity_status=status,
                confidence=0.92 if status == "authentic" else 0.88,
            )
            if status == "adulterated":
                Alert.objects.create(
                    reading=reading,
                    type="adulteration",
                    message=f"Sample: authenticity_status=adulterated (sugar={sugar:.4f}, citric={citric:.4f}, ascorbic={ascorbic:.4f})",
                )
                SystemLog.objects.create(
                    level="WARNING",
                    component="upload",
                    message="Adulterated sample (demo)",
                    metadata={
                        "reading_id": reading.id,
                        "predicted_sugar": sugar,
                        "predicted_citric": citric,
                        "predicted_ascorbic": ascorbic,
                    },
                )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} sample readings (+ predictions, and alerts/logs for adulterated)."))
