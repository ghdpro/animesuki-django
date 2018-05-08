"""AnimeSuki Local Settings File"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Django Debug Toolbar
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
