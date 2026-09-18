from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0035_branch_scoped_stations_positions")]

    operations = [
        migrations.AddField(
            model_name="station", name="organization",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="stations", to="core.organization"),
        ),
        migrations.AddField(
            model_name="position", name="organization",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="positions", to="core.organization"),
        ),
    ]
