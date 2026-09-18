from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0034_userprofile_allowed_platforms")]

    operations = [
        migrations.AlterField(model_name="station", name="name", field=models.CharField(max_length=180)),
        migrations.AlterField(model_name="position", name="name", field=models.CharField(max_length=180)),
        migrations.AddField(
            model_name="station", name="branch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="stations", to="core.branch"),
        ),
        migrations.AddField(
            model_name="position", name="branch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="positions", to="core.branch"),
        ),
        migrations.AddConstraint(
            model_name="station",
            constraint=models.UniqueConstraint(fields=("branch", "name"), name="unique_station_name_per_branch"),
        ),
        migrations.AddConstraint(
            model_name="position",
            constraint=models.UniqueConstraint(fields=("branch", "name"), name="unique_position_name_per_branch"),
        ),
        migrations.AlterModelOptions(name="station", options={"ordering": ["branch__sort_order", "branch__name", "sort_order", "name"]}),
        migrations.AlterModelOptions(name="position", options={"ordering": ["branch__sort_order", "branch__name", "sort_order", "name"]}),
    ]
