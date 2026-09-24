"""Recompute and save confidence for all existing predictions."""
from django.core.management.base import BaseCommand

from readings.ml_inference import compute_confidence
from readings.models import Prediction


class Command(BaseCommand):
    help = "Backfill confidence scores (0–1) for all predictions from their composition values."

    def handle(self, *args, **options):
        updated = 0
        for prediction in Prediction.objects.iterator():
            confidence = compute_confidence(
                prediction.predicted_sugar,
                prediction.predicted_citric,
                prediction.predicted_ascorbic,
                ph=prediction.reading.ph,
            )
            if prediction.confidence != confidence:
                prediction.confidence = confidence
                prediction.save(update_fields=["confidence"])
                updated += 1

        total = Prediction.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated} of {total} prediction(s).")
        )
