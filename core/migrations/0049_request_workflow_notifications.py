from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_publicdocument"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="intakerequest",
            name="assignee",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_intake_requests", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="intakerequest",
            name="sla_due_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="intakerequest",
            name="watchers",
            field=models.ManyToManyField(blank=True, related_name="watched_intake_requests", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="intakerequesthistory",
            name="event",
            field=models.CharField(choices=[("created", "Заявка создана"), ("updated", "Данные изменены"), ("status", "Статус изменён"), ("credentials", "Данные доступа изменены"), ("assignment", "Исполнитель изменён"), ("sla", "Срок SLA изменён")], max_length=24),
        ),
        migrations.CreateModel(
            name="RequestNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("created", "Новая заявка"), ("assigned", "Назначение"), ("status", "Изменение статуса"), ("sla", "Контроль SLA")], max_length=20)),
                ("title", models.CharField(max_length=220)),
                ("message", models.CharField(blank=True, max_length=500)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="request_notifications", to=settings.AUTH_USER_MODEL)),
                ("request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="core.intakerequest")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
