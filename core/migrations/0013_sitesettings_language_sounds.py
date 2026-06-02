from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_sitesettings_externalapiconnection"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="request_notification_sound_ru",
            field=models.FileField(blank=True, upload_to="site/sounds/ru/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="request_notification_sound_uz",
            field=models.FileField(blank=True, upload_to="site/sounds/uz/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="request_notification_sound_uz_cyrl",
            field=models.FileField(blank=True, upload_to="site/sounds/uz-cyrl/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="request_notification_sound_en",
            field=models.FileField(blank=True, upload_to="site/sounds/en/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="telegram_chat_notification_sound_ru",
            field=models.FileField(blank=True, upload_to="site/sounds/ru/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="telegram_chat_notification_sound_uz",
            field=models.FileField(blank=True, upload_to="site/sounds/uz/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="telegram_chat_notification_sound_uz_cyrl",
            field=models.FileField(blank=True, upload_to="site/sounds/uz-cyrl/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="telegram_chat_notification_sound_en",
            field=models.FileField(blank=True, upload_to="site/sounds/en/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="internal_chat_notification_sound_ru",
            field=models.FileField(blank=True, upload_to="site/sounds/ru/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="internal_chat_notification_sound_uz",
            field=models.FileField(blank=True, upload_to="site/sounds/uz/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="internal_chat_notification_sound_uz_cyrl",
            field=models.FileField(blank=True, upload_to="site/sounds/uz-cyrl/"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="internal_chat_notification_sound_en",
            field=models.FileField(blank=True, upload_to="site/sounds/en/"),
        ),
    ]
