from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_generated_passwords(apps, schema_editor):
    IntakeRequest = apps.get_model("core", "IntakeRequest")
    for item in IntakeRequest.objects.exclude(generated_password=""):
        try:
            identify_hasher(item.generated_password)
        except ValueError:
            item.generated_password = make_password(item.generated_password)
            item.save(update_fields=["generated_password"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0025_oneid_sso_defaults"),
    ]

    operations = [
        migrations.RunPython(hash_generated_passwords, migrations.RunPython.noop),
    ]
