"""AnimeSuki Base Settings File"""

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_DIR = os.environ.get('HOME')

# Load secrets from JSON file
import json
secrets = json.loads(open(os.path.join(os.path.dirname(__file__), 'secrets.json')).read())

SECRET_KEY = secrets['secret_key']
ALLOWED_HOSTS = ['.animesuki.com']
SITE_ID = 1
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_FROM_EMAIL = 'webmaster@animesuki.com'
SERVER_EMAIL = 'root@animesuki.com'

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = os.path.join(FILE_DIR, 'static')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required by django-allauth
    'allauth',
    'allauth.account',
    'animesuki.core',
    'animesuki.history',
    'animesuki.media'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_USER_MODEL = 'core.AnimeSukiUser'
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
LOGIN_URL = '/account/login'
LOGIN_REDIRECT_URL = '/account/profile'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_MIN_LENGTH = 3

ROOT_URLCONF = 'animesuki.urls'
WSGI_APPLICATION = 'animesuki.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '',  # unix socket
        'NAME': 'animesuki',
        'USER': 'animesuki',
        'PASSWORD': secrets['database_password']
    }
}

# Log file must be writable by Django server process
LOGFILE = os.path.join(FILE_DIR, 'log', 'animesuki.log')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(message)s [%(name)s.%(funcName)s:%(lineno)d]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(asctime)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'production': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOGFILE,
            'formatter': 'verbose',
            'filters': ['require_debug_false'],
        },
        'debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOGFILE,
            'formatter': 'verbose',
            'filters': ['require_debug_true'],
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'production', 'debug'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'animesuki': {
            'handlers': ['console', 'production', 'debug'],
            'level': 'DEBUG',
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Prefer Argon2 for passwords
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# Date format
from django.conf.locale.en import formats as en_formats
en_formats.DATETIME_FORMAT = 'Y-m-d H:i:s'
en_formats.SHORT_DATETIME_FORMAT = 'Y-m-d H:i'
en_formats.SHORT_DATE_FORMAT = 'Y-m-d'
