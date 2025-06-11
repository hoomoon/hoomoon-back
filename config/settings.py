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

# System Configuration - Configurações específicas do sistema
SYSTEM_NAME = config('SYSTEM_NAME', default='Investment Platform')
SYSTEM_VERSION = config('SYSTEM_VERSION', default='1.0.0')
COMPANY_NAME = config('COMPANY_NAME', default='Financial Services Inc.')
COMPANY_LOGO = config('COMPANY_LOGO', default='')
SYSTEM_THEME_COLOR = config('SYSTEM_THEME_COLOR', default='#1e40af')
REFERRAL_CODE_PREFIX = config('REFERRAL_CODE_PREFIX', default='INV')

# Feature Toggles - Controle de funcionalidades
FEATURES = {
    'REFERRAL_SYSTEM': config('FEATURE_REFERRAL_SYSTEM', default=True, cast=bool),
    'MULTI_CURRENCY': config('FEATURE_MULTI_CURRENCY', default=True, cast=bool),
    'KYC_VERIFICATION': config('FEATURE_KYC_VERIFICATION', default=True, cast=bool),
    'AUTOMATED_YIELDS': config('FEATURE_AUTOMATED_YIELDS', default=True, cast=bool),
    'PIX_PAYMENTS': config('FEATURE_PIX_PAYMENTS', default=True, cast=bool),
    'CRYPTO_PAYMENTS': config('FEATURE_CRYPTO_PAYMENTS', default=True, cast=bool),
    'ADMIN_DASHBOARD': config('FEATURE_ADMIN_DASHBOARD', default=True, cast=bool),
}

# Business Rules - Regras de negócio configuráveis
BUSINESS_RULES = {
    'MIN_DEPOSIT_AMOUNT': config('MIN_DEPOSIT_AMOUNT', default=10.00, cast=float),
    'MAX_DEPOSIT_AMOUNT': config('MAX_DEPOSIT_AMOUNT', default=50000.00, cast=float),
    'REFERRAL_BONUS_PERCENT': config('REFERRAL_BONUS_PERCENT', default=5.0, cast=float),
    'DEFAULT_CURRENCY': config('DEFAULT_CURRENCY', default='USD'),
    'WITHDRAWAL_FEE_PERCENT': config('WITHDRAWAL_FEE_PERCENT', default=2.0, cast=float),
    'MIN_WITHDRAWAL_AMOUNT': config('MIN_WITHDRAWAL_AMOUNT', default=50.00, cast=float),
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',
    # Apps modulares
    'core',
    'users',
    'investments',
    'payments',
    'financial',
    'notifications',
    'referrals',
    'audit',
    # App legado (temporariamente desabilitado para migração)
    # 'api',
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
    # Middlewares customizados para modularização
    'core.middleware.DynamicHeadersMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware.FeatureToggleMiddleware',
    # Middlewares de segurança para sistema financeiro
    'core.middleware.SecurityMiddleware',
    'core.middleware.AuthenticationLoggingMiddleware',
    # Middlewares de auditoria
    'audit.middleware.AuditMiddleware',
    'audit.middleware.RequestTimeMiddleware',
    'audit.middleware.SecurityHeadersMiddleware',
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

AUTH_USER_MODEL = 'users.User'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
# Adicionar testserver para testes
ALLOWED_HOSTS.append('testserver')
ALLOWED_HOSTS.append('localhost')
ALLOWED_HOSTS.append('127.0.0.1')

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

SESSION_COOKIE_DOMAIN = config('COOKIE_DOMAIN')
CSRF_COOKIE_DOMAIN = config('COOKIE_DOMAIN')

# Configurações de segurança para cookies JWT
SESSION_COOKIE_SECURE = config('COOKIE_SECURE', cast=bool)
CSRF_COOKIE_SECURE = config('COOKIE_SECURE', cast=bool)
SESSION_COOKIE_SAMESITE = config('COOKIE_SAMESITE', default='Strict')
CSRF_COOKIE_SAMESITE = config('COOKIE_SAMESITE', default='Strict')

# Configurações extras de segurança para sistema financeiro
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 15 * 60  # 15 minutos (mesmo que access token)

# Configurações de CORS mais restritivas para sistema financeiro
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS_REGEXES = []

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.SecureCookieJWTAuthentication',  # Autenticação segura via cookies
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
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

# ConnectPay
CONNECTPAY_BASE_URL = "https://api.connectpay.vc"
CONNECTPAY_API_SECRET = config('CONNECTPAY_API_SECRET')
if not CONNECTPAY_API_SECRET:
    print("ALERTA: CONNECTPAY_API_SECRET não definida como variável de ambiente.")

CONNECTPAY_WEBHOOK_BASE_URL = config('CONNECTPAY_WEBHOOK_BASE_URL', default="http://localhost:8000")
CONNECTPAY_BENEFICIARY_NAME = config('CONNECTPAY_BENEFICIARY_NAME', default="Nome da Sua Empresa Hoomoon")
CONNECTPAY_WEBHOOK_TOKEN = config('CONNECTPAY_WEBHOOK_TOKEN', default=None)

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
        'api': { # Logger da app 'api' (legado)
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'users': { # Logger da app 'users'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'investments': { # Logger da app 'investments'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'payments': { # Logger da app 'payments'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'financial': { # Logger da app 'financial'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'notifications': { # Logger da app 'notifications'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'referrals': { # Logger da app 'referrals'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
        'core': { # Logger da app 'core'
            'handlers': ['console', 'file_app'],
            'level': API_APP_LOG_LEVEL, # Controlado pela variável
            'propagate': False,
        },
    },
    'root': { # Logger raiz - pega o que não foi especificado acima
        'handlers': ['console', 'file_app'], # Em produção, talvez só 'file_app'
        'level': 'INFO', # Um fallback geral
    }
}