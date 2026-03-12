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
SAMPLE_ROWS = [
    (5.2, 420.0, 26.5, 1.1, 4.8, 0.12, 0.08, "authentic"),
    (5.4, 380.0, 25.8, 0.9, 4.5, 0.11, 0.07, "authentic"),
    (5.1, 450.0, 27.0, 1.2, 5.0, 0.13, 0.09, "authentic"),
    (5.6, 390.0, 26.2, 1.0, 4.2, 0.10, 0.06, "authentic"),
    (4.9, 510.0, 25.0, 1.5, 6.2, 0.18, 0.12, "adulterated"),  # one adulterated -> alert + log
    (5.3, 410.0, 26.0, 1.0, 4.6, 0.11, 0.08, "authentic"),
    (5.2, 430.0, 26.8, 1.1, 4.7, 0.12, 0.07, "authentic"),
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
        # Spread samples: some today, some in past week, some in past month
        for i, (ph, tds, temp, turb, sugar, citric, ascorbic, status) in enumerate(SAMPLE_ROWS):
            # Offset so we have data for daily (today), weekly, monthly
            if i < 2:
                ts = now - timedelta(hours=i)
            elif i < 5:
                ts = now - timedelta(days=i + 1)
            else:
                ts = now - timedelta(days=10 + i)
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
