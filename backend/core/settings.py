from pathlib import Path
import os
import sys
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# Применяем патч для совместимости channels-redis 4.x
try:
    import core.channel_layer_patch
except ImportError:
    pass

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
    'drf_spectacular', 

    # Установленные приложения
    'channels',
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
    # 'axes',  # django-axes для защиты от перебора паролей - временно отключено

    # Наши приложения
    'accounts',
    'crypto',
    'transactions',
    'django_celery_beat',
]

SITE_ID = 2

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.JWTCookieMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.CsrfCookieMiddleware',   
    # 'axes.middleware.AxesMiddleware',  # Должен быть последним - временно отключено
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
# AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', '5'))
# AXES_COOLOFF_TIME = int(os.getenv('AXES_COOLOFF_TIME', '1'))  # в часах
# AXES_LOCKOUT_TEMPLATE = 'account_locked.html'
# AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Блокировка по комбинации пользователь+IP
# AXES_RESET_ON_SUCCESS = True  # Сброс счетчика при успешном входе

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
    # Явное указание использовать drf-spectacular для генерации схемы API
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
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
        'prices': '10/minute',  # Специальный лимит для цен
    }
}

# TRONGrid API Key
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY')

# Blockcypher API Key for Bitcoin
BLOCKCYPHER_API_KEY = os.getenv('BLOCKCYPHER_API_KEY', '')

# TRON Network configuration
TRON_NETWORK = os.getenv('TRON_NETWORK', 'mainnet') # По умолчанию mainnet

if TRON_NETWORK == 'nile':
    TRON_API_URL = 'https://nile.trongrid.io'
    USDT_CONTRACT_ADDRESS = 'TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf'
else: # mainnet
    TRON_API_URL = 'https://api.trongrid.io'
    USDT_CONTRACT_ADDRESS = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'

USDT_TRC20_CONTRACT_ADDRESS = os.getenv("USDT_TRC20_CONTRACT_ADDRESS", "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj")

# Bitcoin HD Wallet xpub key (testnet)
# В реальном проекте этот ключ должен быть в .env файле
BITCOIN_XPUB_KEY = os.getenv('BITCOIN_XPUB_KEY')

# TRON HD Wallet Master Seed
TRON_MASTER_SEED_HEX = os.getenv('TRON_MASTER_SEED_HEX')


ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
       
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
ASGI_APPLICATION = 'core.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
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
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Статические файлы
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки аутентификации
AUTHENTICATION_BACKENDS = (
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

# Время жизни токена подтверждения вывода в часах
WITHDRAWAL_CONFIRMATION_TOKEN_LIFETIME_HOURS = int(os.getenv('WITHDRAWAL_CONFIRMATION_TOKEN_LIFETIME_HOURS', '24'))

# REST Auth настройки
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': SIMPLE_JWT['AUTH_COOKIE'],
    'JWT_AUTH_REFRESH_COOKIE': 'refresh_token',
    'JWT_AUTH_HTTPONLY': SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
    'JWT_AUTH_SAMESITE': SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
    'JWT_AUTH_SECURE': SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    'SESSION_LOGIN': False,
    'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
    'REGISTER_SERIALIZER': 'accounts.serializers.CustomRegisterSerializer',
}

# AllAuth настройки (обновлены для версии 65.11.0)
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_SUBJECT_PREFIX = 'Cryptoobmen - '
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True

# Новые настройки для allauth 65.11.0+
ACCOUNT_LOGIN_METHODS = ['email']
ACCOUNT_SIGNUP_FIELDS = {
    'email': {'required': True},
    'username': {'required': False},
    'first_name': {'required': False},
    'last_name': {'required': False},
}
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'

# Устаревшие настройки заменены на новые
# ACCOUNT_USERNAME_REQUIRED = False  # Убрано
# ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Убрано  
# ACCOUNT_EMAIL_REQUIRED = True  # Убрано

ACCOUNT_RATE_LIMITS = {
    'confirm_email': '5/m',
}
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

SPECTACULAR_SETTINGS = {
    'TITLE': 'Cryptoobmen API',  # Название вашего проекта
    'DESCRIPTION': 'Документация для API проекта Cryptoobmen', # Описание
    'VERSION': '1.0.0',
    # Указываем, что UI должен быть доступен через HTTPS в продакшене
    'SERVE_PUBLIC': True,
    'SERVE_INCLUDE_SCHEMA': False,  # Не показывать голую схему по умолчанию
}


ADMIN_URL = 'admin/'

# ----------------- Celery -----------------
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Настройка очередей для разделения задач
CELERY_TASK_ROUTES = {
    # Критически важные задачи - высокий приоритет
    'crypto.tasks.process_withdrawal': {'queue': 'high_priority'},
    'crypto.tasks.check_withdrawal_confirmation': {'queue': 'high_priority'},
    
    # Консолидация - средний приоритет
    'crypto.tasks_consolidation.consolidate_user_deposits': {'queue': 'medium_priority'},
    'crypto.tasks_consolidation.check_consolidation_confirmations': {'queue': 'medium_priority'},
    
    # Фоновое сканирование - низкий приоритет
    'crypto.tasks.check_blockchain_deposits': {'queue': 'low_priority'},
    'crypto.tasks.process_pending_deposits': {'queue': 'low_priority'},
    'crypto.tasks.process_pending_withdrawals': {'queue': 'low_priority'},
}

# Настройка приоритетов очередей
CELERY_TASK_DEFAULT_QUEUE = 'medium_priority'
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
CELERY_TASK_DEFAULT_PRIORITY = 5

# Настройки производительности
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Обрабатывать по одной задаче за раз
CELERY_TASK_ACKS_LATE = True  # Подтверждать выполнение только после завершения

# Периодические задачи
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'scan_deposits_every_30s': {
        'task': 'crypto.tasks.check_blockchain_deposits',
        'schedule': 30.0,
    },
    'process-pending-withdrawals-every-minute': {
        'task': 'crypto.tasks.process_pending_withdrawals',
        'schedule': 60.0,
    },
    'process-pending-deposits-every-minute': {
        'task': 'crypto.tasks.process_pending_deposits',
        'schedule': 60.0,
    },
    'consolidate-user-deposits-every-5-minutes': {
        'task': 'crypto.tasks_consolidation.consolidate_user_deposits',
        'schedule': 300.0,  # 5 минут
    },
    'check-consolidation-confirmations-every-minute': {
        'task': 'crypto.tasks_consolidation.check_consolidation_confirmations',
        'schedule': 60.0,
    },
    'consolidate_funds_every_5_minutes': {
        'task': 'crypto.tasks.consolidate_funds',
        'schedule': 300.0,  # 300 секунд = 5 минут
    },
}


# ----------------- i18n -----------------
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}

TRON_PLATFORM_PRIVATE_KEY = os.getenv('TRON_PLATFORM_PRIVATE_KEY')

# XUMM (Xaman) API ключи для интеграции с XRP Ledger через XUMM
XAMAN_API_KEY = os.getenv('XAMAN_API_KEY', '')
XAMAN_API_SECRET = os.getenv('XAMAN_API_SECRET', '')

# Ethereum настройки
ETHEREUM_NETWORK = os.getenv('ETHEREUM_NETWORK', 'mainnet')  # mainnet, goerli, sepolia
ETHEREUM_RPC_URL = os.getenv('ETHEREUM_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID')
ETHEREUM_BACKUP_RPC_URL = os.getenv('ETHEREUM_BACKUP_RPC_URL', '')  # Резервный RPC
INFURA_PROJECT_ID = os.getenv('INFURA_PROJECT_ID', '')
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY', '')

# Ethereum контракты
USDT_ERC20_CONTRACT_ADDRESS = os.getenv('USDT_ERC20_CONTRACT_ADDRESS', '0xdAC17F958D2ee523a2206206994597C13D831ec7')
USDC_ERC20_CONTRACT_ADDRESS = os.getenv('USDC_ERC20_CONTRACT_ADDRESS', '0xA0b86a33E6441b8C4505B8C4505B8C4505B8C4505')
DAI_ERC20_CONTRACT_ADDRESS = os.getenv('DAI_ERC20_CONTRACT_ADDRESS', '0x6B175474E89094C44Da98b954EedeAC495271d0F')

# Gas настройки
ETHEREUM_GAS_PRICE_MULTIPLIER = float(os.getenv('ETHEREUM_GAS_PRICE_MULTIPLIER', '1.1'))  # 10% надбавка к базовой цене
ETHEREUM_MAX_GAS_PRICE = int(os.getenv('ETHEREUM_MAX_GAS_PRICE', '100'))  # Максимальная цена газа в Gwei
ETHEREUM_GAS_LIMIT_ETH = int(os.getenv('ETHEREUM_GAS_LIMIT_ETH', '21000'))  # Лимит газа для ETH
ETHEREUM_GAS_LIMIT_ERC20 = int(os.getenv('ETHEREUM_GAS_LIMIT_ERC20', '65000'))  # Лимит газа для ERC-20

BSC_TESTNET_RPC_URL = os.getenv('BSC_TESTNET_RPC_URL', 'https://data-seed-prebsc-1-s1.binance.org:8545/')
BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY', '')  # Получить на https://bscscan.com/apis

# Polygon настройки (только нативная валюта POL)
POLYGON_NETWORK = os.getenv('POLYGON_NETWORK', 'testnet')  # mainnet, amoy (testnet)

# Выбираем правильный RPC URL в зависимости от сети
if POLYGON_NETWORK == 'mainnet':
    POLYGON_RPC_URL = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
    POLYGON_BACKUP_RPC_URL = os.getenv('POLYGON_BACKUP_RPC_URL', 'https://rpc-mainnet.maticvigil.com')
else:  # testnet/amoy
    POLYGON_RPC_URL = os.getenv('POLYGON_TESTNET_RPC_URL', 'https://rpc-amoy.polygon.technology')
    POLYGON_BACKUP_RPC_URL = os.getenv('POLYGON_TESTNET_RPC_URL', 'https://polygon-amoy.blockpi.network/v1/rpc/public')

# Gas настройки для Polygon (POL)
POLYGON_GAS_PRICE_MULTIPLIER = float(os.getenv('POLYGON_GAS_PRICE_MULTIPLIER', '1.1'))
POLYGON_MAX_GAS_PRICE = int(os.getenv('POLYGON_MAX_GAS_PRICE', '50'))  # В Gwei
POLYGON_GAS_LIMIT = int(os.getenv('POLYGON_GAS_LIMIT', '21000'))  # Для POL транзакций
