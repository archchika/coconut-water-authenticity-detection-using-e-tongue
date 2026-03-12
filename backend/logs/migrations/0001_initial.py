# Generated for Phase 5.4 — SystemLog

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("level", models.CharField(db_index=True, max_length=16)),
                ("component", models.CharField(blank=True, max_length=64)),
                ("message", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "logs_systemlogs",
                "ordering": ["-timestamp"],
                "verbose_name_plural": "System logs",
            },
        ),
    ]
