"""
Load daily prototype readings after June 30 with rotating counts: 20, 25, 15, 30, 18.

July 1 → 20 readings, July 2 → 25, July 3 → 15, July 4 → 30, July 5 → 18, then repeats.

Usage:
  python manage.py load_daily_readings_after_june30
  python manage.py load_daily_readings_after_june30 --to-date 2026-07-31
  python manage.py load_daily_readings_after_june30 --clear-range
"""
from datetime import date

from django.core.management.base import BaseCommand

from readings.demo_data import clear_readings_in_range, persist_reading_rows
from readings.june30_validation import (
    POST_VALIDATION_START,
    generate_daily_samples,
    iter_post_validation_days,
)


class Command(BaseCommand):
    help = "Load daily readings after June 30 (counts cycle: 20, 25, 15, 30, 18)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-date",
            default=POST_VALIDATION_START,
            help="First day to load (default: 2026-07-01).",
        )
        parser.add_argument(
            "--to-date",
            default=None,
            help="Last day to load (default: today).",
        )
        parser.add_argument(
            "--clear-range",
            action="store_true",
            help="Delete readings in the date range before loading.",
        )

    def handle(self, *args, **options):
        from_date = options["from_date"]
        to_date = options["to_date"] or date.today().isoformat()

        if options["clear_range"]:
            readings, alerts = clear_readings_in_range(from_date, to_date)
            self.stdout.write(f"Cleared {readings} readings and {alerts} alerts ({from_date} to {to_date}).")

        total = 0
        for date_str, _day_offset, count in iter_post_validation_days(from_date, to_date):
            rows = generate_daily_samples(date_str, count, _day_offset)
            created = persist_reading_rows(rows, date_str)
            total += created
            self.stdout.write(f"  {date_str}: {created} readings")

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {total} daily readings from {from_date} to {to_date}."
        ))
