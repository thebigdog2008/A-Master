"""
WSGI config for realtorx project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application  # noqa I001
import newrelic.agent
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
newrelic.agent.initialize(os.path.join(os.path.dirname(__file__), "newrelic.ini"))
application = newrelic.agent.WSGIApplicationWrapper(application)
