from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0033_remove_siterole_branch_remove_siterole_organization"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="allowed_platforms",
            field=models.ManyToManyField(blank=True, related_name="allowed_users", to="core.platform"),
        ),
    ]
