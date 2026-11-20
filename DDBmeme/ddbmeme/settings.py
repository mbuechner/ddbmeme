import os

from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY') or get_random_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

def _env_bool(name, default='0'):
    return os.environ.get(name, default).strip().lower() in ('1', 'true', 'yes')

USE_X_FORWARDED_HOST = _env_bool('USE_X_FORWARDED_HOST')
if USE_X_FORWARDED_HOST:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ALLOWED_HOSTS: read comma-separated env var and strip whitespace.
# If ALLOW_ALL_HOSTS=1/true is set, allow all hosts (useful inside containers).
_allowed = os.environ.get('ALLOWED_HOSTS')
if _allowed:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
else:
    if _env_bool('ALLOW_ALL_HOSTS'):
        ALLOWED_HOSTS = ['*']
    else:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ddbmeme',
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

ROOT_URLCONF = 'ddbmeme.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # 'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ddbmeme.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

PROJECT_DIR = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(PROJECT_DIR, '../resources')
STATIC_URL = '/resources/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'ERROR'),
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Memegen service configuration (can be overridden via env)
MEMEGEN_BASE_URL = os.environ.get('MEMEGEN_BASE_URL', 'http://localhost:5001')


def _env_int(name, default, minimum):
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except ValueError:
        return default


# Connect, Read timeouts in seconds as comma-separated env var, e.g. '5,20'
try:
    _timeouts = [int(value) for value in os.environ.get('MEMEGEN_TIMEOUT', '5,180').split(',')]
    if len(_timeouts) not in (1, 2) or min(_timeouts) <= 0:
        raise ValueError
    MEMEGEN_TIMEOUT = (_timeouts[0], _timeouts[-1])
except ValueError:
    MEMEGEN_TIMEOUT = (5, 180)

MEMEGEN_RETRY_TOTAL = _env_int('MEMEGEN_RETRY_TOTAL', 0, 0)
MEMEGEN_MAX_CONCURRENCY = _env_int('MEMEGEN_MAX_CONCURRENCY', 2, 1)
MEMEGEN_QUEUE_WAIT_SECONDS = _env_int('MEMEGEN_QUEUE_WAIT_SECONDS', 30, 0)
