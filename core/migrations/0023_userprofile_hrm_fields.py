from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_externalapiconnection_health"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="pnfl",
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="middle_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="birth_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="employee_pinfl",
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="branch",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="organization",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="department",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="position",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="hrm_photo",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="hrm_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="hrm_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
