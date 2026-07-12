import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("current_location", models.CharField(max_length=255)),
                ("pickup_location", models.CharField(max_length=255)),
                ("dropoff_location", models.CharField(max_length=255)),
                (
                    "current_cycle_used_hours",
                    models.DecimalField(decimal_places=2, max_digits=4),
                ),
                ("start_datetime", models.DateTimeField(blank=True, null=True)),
                ("result", models.JSONField(default=dict)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="trip",
            index=models.Index(fields=["-created_at"], name="trip_created_at_idx"),
        ),
        migrations.AddConstraint(
            model_name="trip",
            constraint=models.CheckConstraint(
                check=models.Q(current_cycle_used_hours__gte=0),
                name="trip_cycle_used_gte_0",
            ),
        ),
    ]
