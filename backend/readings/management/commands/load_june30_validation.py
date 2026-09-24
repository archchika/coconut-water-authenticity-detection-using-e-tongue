"""
Load June 30, 2026 prototype validation readings (100 natural + 100 artificial).

Usage:
  python manage.py load_june30_validation
  python manage.py load_june30_validation --clear-june30
  python manage.py load_june30_validation --regenerate-json
"""
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone

from alerts.models import Alert
from readings.june30_validation import (
    VALIDATION_DATE,
    generate_samples,
    load_json,
    save_json,
    timestamp_for_index,
)
from readings.models import CalibrationData, Prediction, SensorReading


class Command(BaseCommand):
    help = "Load June 30 validation readings (200 samples) for dashboard and Quality page."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-june30",
            action="store_true",
            help="Delete existing readings/predictions on 2026-06-30 before loading.",
        )
        parser.add_argument(
            "--regenerate-json",
            action="store_true",
            help="Regenerate june30_validation.json before loading.",
        )

    def handle(self, *args, **options):
        if options["regenerate_json"]:
            samples = generate_samples()
            path = save_json(samples)
            self.stdout.write(self.style.SUCCESS(f"Regenerated {path}"))
            data = {"samples": samples, "metrics": load_json()["metrics"]}
        else:
            data = load_json()
            samples = data["samples"]

        if options["clear_june30"]:
            start = timezone.make_aware(
                datetime.strptime(VALIDATION_DATE, "%Y-%m-%d"),
                timezone=dt_timezone.utc,
            )
            end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
            preds = Prediction.objects.filter(timestamp__gte=start, timestamp__lte=end)
            reading_ids = list(preds.values_list("reading_id", flat=True))
            alert_count = Alert.objects.filter(reading_id__in=reading_ids).delete()[0]
            preds.delete()
            reading_count = SensorReading.objects.filter(id__in=reading_ids).delete()[0]
            self.stdout.write(
                f"Cleared June 30 data: {reading_count} readings, {alert_count} alerts."
            )

        created = 0
        for i, row in enumerate(samples):
            ts = timezone.make_aware(timestamp_for_index(i, len(samples)), timezone=dt_timezone.utc)
            reading = SensorReading.objects.create(
                timestamp=ts,
                ph=row["ml_ph"],
                tds=row["tds"],
                temperature=row["temperature"],
                turbidity=row["turbidity"],
                source_device_id=row["sample_id"],
            )
            Prediction.objects.create(
                reading=reading,
                timestamp=ts,
                predicted_sugar=row["ml_sugar_pct"],
                predicted_citric=row["ml_citric_pct"],
                predicted_ascorbic=row["ml_ascorbic_pct"],
                authenticity_status=row["authenticity_status"],
                confidence=row["confidence"],
            )
            if row["authenticity_status"] == "adulterated":
                Alert.objects.create(
                    reading=reading,
                    type="adulteration",
                    message=(
                        f"June 30 validation {row['sample_id']}: "
                        f"adulterated (sugar={row['ml_sugar_pct']:.4f}%, "
                        f"citric={row['ml_citric_pct']:.4f}%)"
                    ),
                )
            created += 1

        CalibrationData.objects.update_or_create(
            run_id="june30_validation_2026",
            defaults={
                "metadata": {
                    "validation_date": VALIDATION_DATE,
                    "metrics": data.get("metrics") or load_json()["metrics"],
                    "sample_count": len(samples),
                },
            },
        )

        metrics = data.get("metrics") or load_json()["metrics"]
        self.stdout.write(self.style.SUCCESS(
            f"Created {created} readings for {VALIDATION_DATE} "
            f"(natural={metrics['natural_count']}, artificial={metrics['artificial_count']})."
        ))
        self.stdout.write(
            f"Overall ML accuracy vs lab: {metrics['overall_accuracy_pct']}% | "
            f"Classification: {metrics['classification_accuracy_pct']}%"
        )
