import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# BASE_DIR já estava ali antes
BASE_DIR = Path(__file__).resolve().parent.parent

# 1) carrega variáveis do .env (assegure um arquivo .env na raiz do projeto)
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise Exception("SECRET_KEY not set in .env")
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # apps que você adiciona:
    'corsheaders',                       # CORS
    'rest_framework',                    # Django REST Framework
    'rest_framework_simplejwt',          # JWT auth
    'api',                               # sua app de API
 ]

MIDDLEWARE = [
    # CORS deve vir o mais alto possível
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # ou [] se não usar pasta custom
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',   # obrigatória pro admin
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

STATIC_URL = '/static/'

DATABASES = {
     'default': dj_database_url.config(
         default=os.environ.get('DATABASE_URL')
     )
}

AUTH_USER_MODEL = 'api.User'

# 2) Configurações de CORS — ajuste as origens conforme seu Next.js
CORS_ALLOWED_ORIGINS = os.environ.get('ALLOWED_HOSTS')

# se for usar cookies/Credentials:
CORS_ALLOW_CREDENTIALS = True

# 3) Configurações básicas do DRF  Simple JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
