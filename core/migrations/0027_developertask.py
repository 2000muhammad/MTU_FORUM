from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_hash_generated_passwords"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DeveloperTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("new", "Новые"), ("in_progress", "Выполняются"), ("done", "Выполненные"), ("failed", "Не выполненные"), ("done_late", "Выполнено с просрочкой"), ("approval", "На утверждении"), ("revision", "Отправленные на доработку"), ("resumed", "Возобновленные"), ("familiarized", "Ознакомленные")], default="new", max_length=32)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("is_viewed", models.BooleanField(default=False)),
                ("priority", models.PositiveSmallIntegerField(default=2)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_developer_tasks", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_developer_tasks", to=settings.AUTH_USER_MODEL)),
                ("coexecutors", models.ManyToManyField(blank=True, related_name="coexecuted_developer_tasks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
