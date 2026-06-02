from django.db import migrations, models


def update_mobile_app_name(apps, schema_editor):
    api_configuration = apps.get_model("core", "ApiConfiguration")
    api_configuration.objects.filter(mobile_app_name="E-NAKL Mobile").update(
        mobile_app_name="MTU FORUM Mobile"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_remove_webplatform_code_webplatform_image_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apiconfiguration",
            name="mobile_app_name",
            field=models.CharField(default="MTU FORUM Mobile", max_length=120),
        ),
        migrations.RunPython(update_mobile_app_name, migrations.RunPython.noop),
    ]
