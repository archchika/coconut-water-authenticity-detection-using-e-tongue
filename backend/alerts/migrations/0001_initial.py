# Generated for Phase 5.4 — Alert

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("readings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("type", models.CharField(db_index=True, max_length=64)),
                ("message", models.TextField(blank=True)),
                ("resolved", models.BooleanField(db_index=True, default=False)),
                ("reading", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="alerts", to="readings.sensorreading")),
            ],
            options={
                "db_table": "alerts_alerts",
                "ordering": ["-timestamp"],
            },
        ),
    ]
