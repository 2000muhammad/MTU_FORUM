from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0036_organization_scoped_stations_positions"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="allowed_stations",
            field=models.ManyToManyField(blank=True, related_name="allowed_users", to="core.station"),
        ),
    ]
