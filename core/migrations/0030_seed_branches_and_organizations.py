from django.db import migrations


def seed_directories(apps, schema_editor):
    Branch = apps.get_model("core", "Branch")
    Organization = apps.get_model("core", "Organization")
    UserProfile = apps.get_model("core", "UserProfile")

    pairs = UserProfile.objects.exclude(organization="").values_list("branch", "organization").distinct()
    for branch_name, organization_name in pairs:
        branch_name = (branch_name or "").strip() or "Без филиала"
        organization_name = (organization_name or "").strip()
        if not organization_name:
            continue
        branch, _ = Branch.objects.get_or_create(name=branch_name)
        Organization.objects.get_or_create(branch=branch, name=organization_name)

    branch_names = UserProfile.objects.exclude(branch="").values_list("branch", flat=True).distinct()
    for branch_name in branch_names:
        branch_name = (branch_name or "").strip()
        if branch_name:
            Branch.objects.get_or_create(name=branch_name)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0029_branch_organization_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_directories, migrations.RunPython.noop),
    ]
