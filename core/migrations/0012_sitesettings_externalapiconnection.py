from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_update_api_mobile_app_name_default"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_name", models.CharField(default="MTU FORUM", max_length=120)),
                ("site_logo", models.FileField(blank=True, upload_to="site/branding/")),
                ("site_favicon", models.FileField(blank=True, upload_to="site/branding/")),
                ("site_image", models.FileField(blank=True, upload_to="site/branding/")),
                ("notification_sound_enabled", models.BooleanField(default=True)),
                ("request_notification_sound", models.FileField(blank=True, upload_to="site/sounds/")),
                ("telegram_chat_notification_sound", models.FileField(blank=True, upload_to="site/sounds/")),
                ("internal_chat_notification_sound", models.FileField(blank=True, upload_to="site/sounds/")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Site settings",
                "verbose_name_plural": "Site settings",
            },
        ),
        migrations.CreateModel(
            name="ExternalApiConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("base_url", models.URLField(blank=True, max_length=500)),
                ("auth_header", models.CharField(default="X-API-KEY", max_length=80)),
                ("api_key", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["sort_order", "name"],
            },
        ),
    ]
