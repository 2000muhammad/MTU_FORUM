from django.db import migrations
from django.utils.text import slugify


def fill_codes(apps, schema_editor):
    for model_name in ("Station", "Branch", "Organization", "Platform", "SiteRole"):
        model = apps.get_model("core", model_name)
        for item in model.objects.filter(code="").order_by("pk"):
            max_length = item._meta.get_field("code").max_length
            base = slugify(item.name or "", allow_unicode=True).replace("-", "_") or "item"
            base = base[:max_length]
            candidate = base
            counter = 2
            queryset = model.objects.exclude(pk=item.pk)
            if model_name == "Organization":
                queryset = queryset.filter(branch_id=item.branch_id)
            while queryset.filter(code=candidate).exists():
                suffix = f"_{counter}"
                candidate = f"{base[:max_length - len(suffix)]}{suffix}"
                counter += 1
            item.code = candidate
            item.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_seed_branches_and_organizations"),
    ]

    operations = [
        migrations.RunPython(fill_codes, migrations.RunPython.noop),
    ]
