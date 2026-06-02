from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_userprofile_hrm_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_client_id",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_client_secret",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_authorize_url",
            field=models.URLField(default="https://id.egov.uz/oz"),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_token_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_userinfo_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_scope",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_verify_ssl",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="oneid_auto_create_user",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="eimzo_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="apiconfiguration",
            name="eimzo_oneid_method",
            field=models.CharField(default="EIMZO", max_length=32),
        ),
    ]
