from django.db import migrations


def create_quotes_connection(apps, schema_editor):
    ExternalApiConnection = apps.get_model("core", "ExternalApiConnection")
    ExternalApiConnection.objects.get_or_create(
        name="API Ninjas Quotes",
        defaults={
            "purpose": "generic",
            "base_url": "https://api.api-ninjas.com/v2/randomquotes",
            "method": "GET",
            "healthcheck_url": "https://api.api-ninjas.com/v2/quoteoftheday",
            "auth_header": "X-Api-Key",
            "timeout_seconds": 8,
            "is_active": True,
            "sort_order": 40,
            "notes": "Random wisdom quotes for the dashboard. Add the API Ninjas key here.",
        },
    )


def remove_quotes_connection(apps, schema_editor):
    apps.get_model("core", "ExternalApiConnection").objects.filter(
        name="API Ninjas Quotes", api_key=""
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0049_request_workflow_notifications")]
    operations = [migrations.RunPython(create_quotes_connection, remove_quotes_connection)]
