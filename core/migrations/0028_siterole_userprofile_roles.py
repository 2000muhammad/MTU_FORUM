from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_roles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("core", "UserProfile")
    SiteRole = apps.get_model("core", "SiteRole")

    defaults = [
        {
            "name": "Пользователь",
            "code": "user",
            "description": "Базовая роль: Dashboard, сообщения и профиль.",
            "is_builtin": True,
            "can_dashboard": True,
            "can_messages": True,
            "can_profile": True,
            "sort_order": 1,
        },
        {
            "name": "Сотрудник",
            "code": "staff",
            "description": "Операционная роль: заявки, чаты, задания и программисты.",
            "is_builtin": True,
            "is_staff_role": True,
            "can_dashboard": True,
            "can_messages": True,
            "can_requests": True,
            "can_chats": True,
            "can_programmers": True,
            "can_tasks": True,
            "can_profile": True,
            "sort_order": 2,
        },
        {
            "name": "Суперадмин",
            "code": "superadmin",
            "description": "Полный доступ ко всем разделам сайта.",
            "is_builtin": True,
            "is_staff_role": True,
            "is_admin_role": True,
            "can_dashboard": True,
            "can_messages": True,
            "can_requests": True,
            "can_chats": True,
            "can_programmers": True,
            "can_tasks": True,
            "can_users": True,
            "can_directories": True,
            "can_api_settings": True,
            "can_site_settings": True,
            "can_logs": True,
            "can_profile": True,
            "sort_order": 3,
        },
    ]

    roles = {}
    for item in defaults:
        role, _ = SiteRole.objects.update_or_create(code=item["code"], defaults=item)
        roles[item["code"]] = role

    for user in User.objects.all():
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if user.is_superuser:
            profile.roles.add(roles["superadmin"])
        elif user.is_staff:
            profile.roles.add(roles["staff"])
        else:
            profile.roles.add(roles["user"])


def unseed_roles(apps, schema_editor):
    SiteRole = apps.get_model("core", "SiteRole")
    SiteRole.objects.filter(code__in=["user", "staff", "superadmin"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_developertask"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("code", models.SlugField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_builtin", models.BooleanField(default=False)),
                ("is_staff_role", models.BooleanField(default=False)),
                ("is_admin_role", models.BooleanField(default=False)),
                ("can_dashboard", models.BooleanField(default=True)),
                ("can_messages", models.BooleanField(default=True)),
                ("can_requests", models.BooleanField(default=False)),
                ("can_chats", models.BooleanField(default=False)),
                ("can_programmers", models.BooleanField(default=False)),
                ("can_tasks", models.BooleanField(default=False)),
                ("can_users", models.BooleanField(default=False)),
                ("can_directories", models.BooleanField(default=False)),
                ("can_api_settings", models.BooleanField(default=False)),
                ("can_site_settings", models.BooleanField(default=False)),
                ("can_logs", models.BooleanField(default=False)),
                ("can_profile", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["sort_order", "name"]},
        ),
        migrations.AddField(
            model_name="userprofile",
            name="roles",
            field=models.ManyToManyField(blank=True, related_name="users", to="core.siterole"),
        ),
        migrations.RunPython(seed_roles, unseed_roles),
    ]
