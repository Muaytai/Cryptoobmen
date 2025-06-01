from pathlib import Path
import os
import sys
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# Загрузка переменных окружения из .env файла
from dotenv import load_dotenv

# Определяем, какой файл с переменными окружения использовать
if os.environ.get('ENV_FILE'):  # Если переменная ENV_FILE установлена (в Docker)
    env_path = Path(__file__).resolve().parent.parent / os.environ.get('ENV_FILE')
else:  # Локальная разработка
    env_path = Path(__file__).resolve().parent.parent / '.env.backend'
   
# Загружаем переменные окружения
load_dotenv(dotenv_path=env_path)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY must be set in environment variables')

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS and not DEBUG:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be set in production')

# Указываем кастомную модель пользователя
AUTH_USER_MODEL = 'accounts.User'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Установленные приложения
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.yandex',
    
    # Приложения для безопасности
    'django_recaptcha',  # django-recaptcha
    'axes',  # django-axes для защиты от перебора паролей

    # Наши приложения
    'accounts',
    'crypto',
    'transactions',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.JWTCookieMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.CsrfCookieMiddleware',
    'core.middleware.CorsMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'axes.middleware.AxesMiddleware',  # Должен быть последним
]

# Настройки безопасности
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 3153600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Настройки reCAPTCHA
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_REQUIRED_SCORE = float(os.getenv('RECAPTCHA_REQUIRED_SCORE', '0.85'))
RECAPTCHA_DEFAULT_ACTION = 'generic'
RECAPTCHA_DOMAIN = 'www.recaptcha.net'  # Для работы в России

# Настройки Axes (защита от перебора паролей)
AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', '5'))
AXES_COOLOFF_TIME = int(os.getenv('AXES_COOLOFF_TIME', '1'))  # в часах
AXES_LOCKOUT_TEMPLATE = 'account_locked.html'
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Блокировка по комбинации пользователь+IP
AXES_RESET_ON_SUCCESS = True  # Сброс счетчика при успешном входе

# Настройки кэширования
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 минут
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Настройки сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1209600  # 2 недели
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_DOMAIN = None
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Важно для безопасности

# Настройки REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON_RATE', '100/day'),
        'user': os.getenv('THROTTLE_USER_RATE', '1000/day'),
        'login': os.getenv('THROTTLE_LOGIN_RATE', '5/minute'),
        'register': os.getenv('THROTTLE_REGISTER_RATE', '10/hour'),
        'dj_rest_auth': '5/minute',
    }
}

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ] if DEBUG else [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
        'CONN_MAX_AGE': 60,
    }
}

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Локализация
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки аутентификации
AUTHENTICATION_BACKENDS = (
    # AxesStandaloneBackend должен быть первым
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Frontend и Backend URLs
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000' if DEBUG else None)
if not FRONTEND_URL and not DEBUG:
    raise ImproperlyConfigured('FRONTEND_URL must be set in production')

# Backend URL для формирования ссылок в письмах
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000' if DEBUG else None)
if not BACKEND_URL and not DEBUG:
    raise ImproperlyConfigured('BACKEND_URL must be set in production')

# CORS настройки
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'access-control-allow-credentials',
    'access-control-allow-origin',
]

# CSRF настройки
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_USE_SESSIONS = False
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_DOMAIN = None

# Email настройки
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Настройки для писем
EMAIL_SUBJECT_PREFIX = 'Cryptoobmen - '
EMAIL_TIMEOUT = 30  # таймаут в секундах

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'logs' / 'django.log'),
            'formatter': 'verbose',
            'mode': 'a',
        } if not DEBUG else {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'accounts': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'crypto': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'transactions': {
            'handlers': ['console'] if DEBUG else ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# JWT настройки
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'AUTH_COOKIE': 'access_token',  
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_COOKIE_SECURE': False,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',
}

# REST Auth настройки
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': SIMPLE_JWT['AUTH_COOKIE'],
    'JWT_AUTH_REFRESH_COOKIE': 'refresh_token',
    'JWT_AUTH_HTTPONLY': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
    'JWT_AUTH_SAMESITE': SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
    'JWT_AUTH_SECURE': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    'SESSION_LOGIN': False,
}

# AllAuth настройки
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_SUBJECT_PREFIX = 'Cryptoobmen - '
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 180
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = f"{FRONTEND_URL}/verify-email"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = f"{FRONTEND_URL}/verify-email"
LOGIN_REDIRECT_URL = f"{FRONTEND_URL}/profile"
ACCOUNT_EMAIL_CONFIRMATION_URL = f"{FRONTEND_URL}/verify-email/%(key)s/"

# Настройки для социальной авторизации
SOCIALACCOUNT_AUTO_SIGNUP = True  # Автоматическая регистрация через соцсети
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Не требуем подтверждения email для соцсетей
SOCIALACCOUNT_QUERY_EMAIL = True  # Запрашиваем email у провайдера
SOCIALACCOUNT_LOGIN_ON_GET = True  # Авторизация без подтверждения
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account'
        }
    },
    'yandex': {
        'APP': {
            'client_id': os.getenv('YANDEX_CLIENT_ID'),
            'secret': os.getenv('YANDEX_CLIENT_SECRET'),
            'key': ''
        }
    }
}

ADMIN_URL = 'admin/'

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]