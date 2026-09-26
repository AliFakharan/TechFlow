"""WSGI config for TechFlow."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techflow.settings")

application = get_wsgi_application()
