from django.urls import path

from . import views


urlpatterns = [
    path("intake/telegram/", views.telegram_intake_api, name="telegram_intake_api"),
    path("chat/incoming/", views.telegram_chat_incoming_api, name="telegram_chat_incoming_api"),
    path("chat/threads/", views.telegram_chat_threads_api, name="telegram_chat_threads_api"),
    path("intake/telegram/summary/", views.telegram_intake_summary_api, name="telegram_intake_summary_api"),
    path("dashboard/requests/", views.dashboard_requests_api, name="dashboard_requests_api"),
    path("notifications/state/", views.notification_state_api, name="notification_state_api"),
    path("react/bootstrap/", views.react_bootstrap_api, name="react_bootstrap_api"),
    path("react/public/", views.react_public_api, name="react_public_api"),
    path("react/captcha/", views.react_captcha_api, name="react_captcha_api"),
    path("react/login/", views.react_login_api, name="react_login_api"),
    path("react/logout/", views.react_logout_api, name="react_logout_api"),
    path("react/requests/<int:pk>/", views.react_request_api, name="react_request_api"),
    path("auth/oneid/", views.oneid_login_start, name="oneid_login"),
    path("auth/oneid/callback/", views.oneid_callback, name="oneid_callback"),
    path("auth/eimzo/", views.eimzo_login_start, name="eimzo_login"),
    path("auth/face/", views.face_login_view, name="face_login"),
    path("react/directories/<str:section>/", views.react_directory_api, name="react_directory_api"),
    path("public/stations/", views.public_stations_api, name="public_stations_api"),
    path("public/positions/", views.public_positions_api, name="public_positions_api"),
    path("public/platforms/", views.public_platforms_api, name="public_platforms_api"),
    path("public/web-platforms/", views.public_web_platforms_api, name="public_web_platforms_api"),
    path("public/subscription-channels/", views.public_subscription_channels_api, name="public_subscription_channels_api"),
    path("mobile/config/", views.mobile_config_api, name="mobile_config_api"),
]
