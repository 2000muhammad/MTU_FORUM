from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

from django.urls import include, path

from core import views



urlpatterns = [

    path("admin/", admin.site.urls),

    path("api/", include("core.api_urls")),

]



urlpatterns += i18n_patterns(

    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("requests/", views.requests_view, name="requests"),
    path("programmers/", views.programmers_view, name="programmers"),
    path("tasks/", views.developer_tasks_view, name="developer_tasks"),
    path("tasks/create/", views.developer_task_create, name="developer_task_create"),
    path("tasks/<int:pk>/edit/", views.developer_task_edit, name="developer_task_edit"),
    path("tasks/<int:pk>/action/", views.developer_task_action, name="developer_task_action"),

    path("login/", views.LoginView.as_view(), name="login"),
    # RU: OneID/E-IMZO routes: старт входа и callback после ответа SSO.
    # UZ: OneID/E-IMZO routes: kirishni boshlash va SSO javobidan keyingi callback.
    # EN: OneID/E-IMZO routes: login start and callback after the SSO response.
    path("login/oneid/", views.oneid_login_start, name="oneid_login"),
    path("login/eimzo/", views.eimzo_login_start, name="eimzo_login"),
    path("login/oneid/callback/", views.oneid_callback, name="oneid_callback"),
    path("login/face/", views.face_login_view, name="face_login"),

    path("logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),
    path("messages/", views.internal_messages_view, name="internal_messages"),
    path("messages/<int:chat_id>/", views.internal_messages_view, name="internal_messages_detail"),
    path("web-platforms/<int:pk>/open/", views.open_web_platform, name="open_web_platform"),
    path("web-platforms/<int:pk>/favorite/", views.toggle_web_platform_favorite, name="toggle_web_platform_favorite"),
    path("settings/", views.settings_view, name="settings"),
    path("settings/excel/<str:section>/<str:mode>/", views.dictionary_excel_view, name="dictionary_excel"),
    path("settings/api/", views.api_settings_view, name="api_settings"),
    path("site-settings/", views.site_settings_view, name="site_settings"),
    path("site-settings/database/export/", views.database_export_view, name="database_export"),
    path("site-settings/database/import/", views.database_import_view, name="database_import"),
    path("settings/<str:section>/", views.settings_view, name="settings_section"),
    path("logs/", views.site_logs_view, name="site_logs"),
    path("users/", views.users_view, name="users"),
    path("managers/", views.manager_accounts_view, name="manager_accounts"),
    path("requests/<int:pk>/edit/", views.request_edit, name="request_edit"),

    path("chats/", views.admin_chat_list, name="admin_chat_list"),
    path("chats/thread/<int:thread_id>/", views.admin_chat_thread_detail, name="admin_chat_thread_detail"),
    path("chats/<int:telegram_id>/photo/", views.telegram_profile_photo, name="telegram_profile_photo"),
    path("chats/<int:telegram_id>/", views.admin_chat_detail, name="admin_chat_detail"),

)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
