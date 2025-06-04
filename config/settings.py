# config/settings.py
from pathlib import Path
from decouple import config, Csv # type: ignore
import dj_database_url # type: ignore
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DJANGO_DEBUG', cast=bool)

CONSOLE_LOG_LEVEL = config('CONSOLE_LOG_LEVEL', default='DEBUG' if DEBUG else 'INFO', cast=str).upper()
FILE_LOG_LEVEL = config('FILE_LOG_LEVEL', default='DEBUG' if DEBUG else 'INFO', cast=str).upper()
API_APP_LOG_LEVEL = config('API_APP_LOG_LEVEL', default='DEBUG' if DEBUG else 'INFO', cast=str).upper()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
  "default": dj_database_url.config(
      default=config('DATABASE_URL'),
      conn_max_age=600, 
      ssl_require=not DEBUG
      )
}

AUTH_USER_MODEL = 'api.User'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

SESSION_COOKIE_DOMAIN = config('COOKIE_DOMAIN')
CSRF_COOKIE_DOMAIN = config('COOKIE_DOMAIN')

SESSION_COOKIE_SECURE = config('COOKIE_SECURE', cast=bool)
CSRF_COOKIE_SECURE = config('COOKIE_SECURE', cast=bool)
SESSION_COOKIE_SAMESITE = config('COOKIE_SAMESITE', default='None')
CSRF_COOKIE_SAMESITE = config('COOKIE_SAMESITE', default='None')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ALLOWED_HOSTS.append('.ngrok-free.app')

# CoinPayments
COINPAYMENTS_PUBLIC_KEY = config('COINPAYMENTS_PUBLIC_KEY')
COINPAYMENTS_PRIVATE_KEY = config('COINPAYMENTS_PRIVATE_KEY')
COINPAYMENTS_IPN_SECRET = config('COINPAYMENTS_IPN_SECRET')
COINPAYMENTS_MERCHANT_ID = config('COINPAYMENTS_MERCHANT_ID')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno} {process:d} {thread:d} {message}', # Adicionado :lineno
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': CONSOLE_LOG_LEVEL, # Controlado pela variável
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_app': { # Handler de arquivo para sua app e erros críticos
            'level': FILE_LOG_LEVEL, # Controlado pela variável
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/app.log', # Log específico da aplicação
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5, # Aumentamos um pouco o backup
            'formatter': 'verbose',
        },
        'file_django': { # Handler de arquivo para logs do Django (menos verboso)
            'level': 'INFO', # Geralmente INFO é suficiente para o Django em produção
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 2,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_django'], # Logs do Django vão para o console e seu arquivo
            'level': 'INFO', # Mesmo que FILE_LOG_LEVEL seja DEBUG, o Django só logará INFO aqui
            'propagate': False, # Para não duplicar no root se o level for menor
        },
        'django.request': { # Especificamente para erros de requisição HTTP 5XX
            'handlers': ['file_app'], # Erros de servidor vão para o log da app
            'level': 'ERROR',
            'propagate': False,
        },
        'api': { # Logger da sua app 'api'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        # Adicione loggers para outras apps suas aqui, se necessário
    },
    'root': { # Logger raiz - pega o que não foi especificado acima
        'handlers': ['console', 'file_app'], # Em produção, talvez só 'file_app'
        'level': 'INFO', # Um fallback geral
    }
}