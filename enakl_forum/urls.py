from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

from django.urls import include, path

from core import views



urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.api_urls")),
    path("app/", views.frontend_redirect, name="react_app_global"),
    path("app/<path:path>/", views.frontend_redirect, name="react_app_global_path"),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Compatibility only: Django never renders the user interface. Old links are
# sent to the standalone React application.
urlpatterns += [
    path("", views.frontend_redirect, name="index"),
    path("<path:path>", views.frontend_redirect, name="frontend_redirect"),
]
