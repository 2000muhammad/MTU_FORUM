from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_alter_adminchatthread_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalapiconnection",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("generic", "Generic API"),
                    ("face_id", "Face ID"),
                    ("hrm", "HRM"),
                    ("data_sync", "Data sync"),
                    ("notification", "Notification"),
                ],
                default="generic",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="method",
            field=models.CharField(choices=[("GET", "GET"), ("POST", "POST")], default="POST", max_length=8),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="healthcheck_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="timeout_seconds",
            field=models.PositiveSmallIntegerField(default=15),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="last_status_code",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="last_checked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalapiconnection",
            name="last_error",
            field=models.TextField(blank=True),
        ),
    ]
