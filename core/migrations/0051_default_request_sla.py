from datetime import timedelta

from django.db import migrations, models
from django.db.models import F

import core.models


def backfill_request_sla(apps, schema_editor):
    IntakeRequest = apps.get_model("core", "IntakeRequest")
    IntakeRequest.objects.filter(
        status__in=["new", "blocked"],
        sla_due_at__isnull=True,
    ).update(sla_due_at=F("created_at") + timedelta(hours=24))


class Migration(migrations.Migration):
    dependencies = [("core", "0050_api_ninjas_quotes_connection")]

    operations = [
        migrations.RunPython(backfill_request_sla, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="intakerequest",
            name="sla_due_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                default=core.models.default_request_sla_due_at,
            ),
        ),
    ]
