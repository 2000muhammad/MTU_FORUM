import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "enakl_forum.settings")
application = get_asgi_application()
