from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0045_userpresence"),
    ]
    operations = [
        migrations.CreateModel(
            name="PeopleImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("users", "Пользователи"), ("managers", "Менеджеры")], max_length=16)),
                ("status", models.CharField(choices=[("preview", "Предпросмотр"), ("queued", "В очереди"), ("running", "Выполняется"), ("completed", "Завершён"), ("failed", "Ошибка")], db_index=True, default="preview", max_length=16)),
                ("filename", models.CharField(max_length=255)),
                ("rows", models.JSONField(default=list)),
                ("errors", models.JSONField(default=list)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("processed_rows", models.PositiveIntegerField(default=0)),
                ("created_count", models.PositiveIntegerField(default=0)),
                ("updated_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="people_import_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
