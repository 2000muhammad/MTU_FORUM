from django.db import migrations, models


ONEID_SSO_URL = "https://sso.egov.uz/sso/oauth/Authorization.do"


def fill_oneid_sso_defaults(apps, schema_editor):
    # RU: Миграция обновляет старые пустые/id.egov.uz значения на официальный SSO endpoint.
    # UZ: Migratsiya eski bo'sh/id.egov.uz qiymatlarni rasmiy SSO endpointga almashtiradi.
    # EN: Migration replaces old empty/id.egov.uz values with the official SSO endpoint.
    ApiConfiguration = apps.get_model("core", "ApiConfiguration")
    for config in ApiConfiguration.objects.all():
        changed = False
        if not config.oneid_authorize_url or config.oneid_authorize_url.startswith("https://id.egov.uz"):
            config.oneid_authorize_url = ONEID_SSO_URL
            changed = True
        if not config.oneid_token_url:
            config.oneid_token_url = ONEID_SSO_URL
            changed = True
        if not config.oneid_userinfo_url:
            config.oneid_userinfo_url = ONEID_SSO_URL
            changed = True
        if changed:
            config.save(update_fields=["oneid_authorize_url", "oneid_token_url", "oneid_userinfo_url", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_apiconfiguration_oneid_eimzo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apiconfiguration",
            name="oneid_authorize_url",
            field=models.URLField(default=ONEID_SSO_URL),
        ),
        migrations.AlterField(
            model_name="apiconfiguration",
            name="oneid_token_url",
            field=models.URLField(blank=True, default=ONEID_SSO_URL),
        ),
        migrations.AlterField(
            model_name="apiconfiguration",
            name="oneid_userinfo_url",
            field=models.URLField(blank=True, default=ONEID_SSO_URL),
        ),
        migrations.RunPython(fill_oneid_sso_defaults, migrations.RunPython.noop),
    ]
