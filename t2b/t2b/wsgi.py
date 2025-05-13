"""
WSGI config for t2b project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t2b.settings")

# application = get_wsgi_application()

import os

from django.core.wsgi import get_wsgi_application
settings_module = 't2b.deployment' if 'WEBSITE_HOSTNAME' in os.environ else 't2b.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()