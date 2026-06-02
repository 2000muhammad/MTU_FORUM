from django.urls import path

from . import views


urlpatterns = [
    path("intake/telegram/", views.telegram_intake_api, name="telegram_intake_api"),
    path("chat/incoming/", views.telegram_chat_incoming_api, name="telegram_chat_incoming_api"),
    path("chat/threads/", views.telegram_chat_threads_api, name="telegram_chat_threads_api"),
    path("intake/telegram/summary/", views.telegram_intake_summary_api, name="telegram_intake_summary_api"),
    path("dashboard/requests/", views.dashboard_requests_api, name="dashboard_requests_api"),
    path("notifications/state/", views.notification_state_api, name="notification_state_api"),
    path("public/stations/", views.public_stations_api, name="public_stations_api"),
    path("public/positions/", views.public_positions_api, name="public_positions_api"),
    path("public/platforms/", views.public_platforms_api, name="public_platforms_api"),
    path("public/web-platforms/", views.public_web_platforms_api, name="public_web_platforms_api"),
    path("public/subscription-channels/", views.public_subscription_channels_api, name="public_subscription_channels_api"),
    path("mobile/config/", views.mobile_config_api, name="mobile_config_api"),
]
