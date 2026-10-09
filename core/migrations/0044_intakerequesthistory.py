from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def create_initial_history(apps, schema_editor):
    IntakeRequest = apps.get_model("core", "IntakeRequest")
    IntakeRequestHistory = apps.get_model("core", "IntakeRequestHistory")
    status_labels = {"new": "Новая", "done": "Сделано", "blocked": "Заблокирована"}
    rows = [
        IntakeRequestHistory(
            request_id=item.id,
            event="created",
            changes={"Статус": {"old": "—", "new": status_labels.get(item.status, item.status)}},
            to_status=item.status,
            created_at=item.created_at,
        )
        for item in IntakeRequest.objects.all().iterator()
    ]
    IntakeRequestHistory.objects.bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_adminchatmessage_telegram_username_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IntakeRequestHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(choices=[("created", "Заявка создана"), ("updated", "Данные изменены"), ("status", "Статус изменён"), ("credentials", "Данные доступа изменены")], max_length=24)),
                ("changes", models.JSONField(blank=True, default=dict)),
                ("from_status", models.CharField(blank=True, max_length=16)),
                ("to_status", models.CharField(blank=True, max_length=16)),
                ("telegram_notified", models.BooleanField(default=False)),
                ("telegram_error", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="intake_request_changes", to=settings.AUTH_USER_MODEL)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="core.intakerequest")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.RunPython(create_initial_history, migrations.RunPython.noop),
    ]
