from pathlib import Path
from datetime import timedelta

from celery.schedules import crontab
from decouple import config
import dj_database_url


from dotenv import load_dotenv

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)


def _csv(value):
    """Vergul bilan ajratilgan env qiymatini ro'yxatga aylantiradi."""
    return [item.strip() for item in value.split(',') if item.strip()]


ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='dtm-test.onrender.com,localhost,127.0.0.1',
    cast=_csv,
)

# Render kabi platformalar host nomini shu env orqali beradi.
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


AUTH_USER_MODEL = "account.User"

# ---------------------------------------------------------------------------
# Kirish usullari. Android/web -> Google, iPhone/iPad -> Apple ID.
# ---------------------------------------------------------------------------
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID")

# Apple "Sign in with Apple" `aud` qiymatlari: iOS bundle id va (bo'lsa) web
# Services ID. Vergul bilan bir nechtasini berish mumkin. Bo'sh bo'lsa Apple
# orqali kirish o'chirilgan hisoblanadi va endpoint 400 qaytaradi.
APPLE_CLIENT_IDS = config('APPLE_CLIENT_IDS', default='', cast=_csv)

# ---------------------------------------------------------------------------
# Telegram: obuna arizasi admin bilan shu yerda bog'lanadi.
# ---------------------------------------------------------------------------
ADMIN_TELEGRAM_LINK = config('ADMIN_TELEGRAM_LINK', default='https://t.me/akobir_ETA')
# Bot token va chat id sozlansa ariza adminga AVTOMATIK yuboriladi.
# Sozlanmasa ariza baribir bazada qoladi va admin panelda ko'rinadi.
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_ADMIN_CHAT_ID = config('TELEGRAM_ADMIN_CHAT_ID', default='')


# Application definition

DJANGO_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]



LOCAL_APPS = [
    'account',
    'common',
    'notifications',
    'billing',
    'progress',
    'testengine',
    'catalog',
    'rating',
    'dashboard'
]


EXTERNAL_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
]


INSTALLED_APPS = DJANGO_APPS + EXTERNAL_APPS + LOCAL_APPS


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Admin paneli va Django xabarlari foydalanuvchi tilida chiqishi uchun.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]





# ---------------------------------------------------------------------------
# CORS — brauzer, mobil ilova va server-mijozlar uchun.
#
# MUHIM: mahalliy (native) mobil ilovalar `Origin` header YUBORMAYDI, shuning
# uchun CORS ular uchun umuman to'siq emas — iPhone, Samsung yoki boshqa
# Android qurilma to'g'ridan-to'g'ri ulanaveradi. CORS faqat brauzer va
# WebView (Capacitor/Cordova/Ionic) mijozlariga tegishli, quyidagi regex'lar
# aynan o'shalar uchun.
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://localhost:5174,http://localhost:3000',
    cast=_csv,
)

# Hibrid mobil ilovalar (Capacitor / Ionic / Cordova) va lokal dev portlari.
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^capacitor://.*$',
    r'^ionic://.*$',
    r'^http://localhost(:\d+)?$',
    r'^http://127\.0\.0\.1(:\d+)?$',
    r'^https://.*\.onrender\.com$',
]

# Kerak bo'lsa (masalan public API) env orqali hammaga ochish mumkin.
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]

# `X-Language` — mobil ilova tilni shu header orqali beradi.
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'accept-language',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-language',
    'x-app-version',
    'x-device-id',
    'x-platform',
]

# Fayl yuklashda (savol rasmi) brauzer shu headerlarni o'qiy olishi kerak.
CORS_EXPOSE_HEADERS = ['content-disposition', 'content-language']

CORS_PREFLIGHT_MAX_AGE = 86400

# Django 4+ proxy ortida admin/POST so'rovlari uchun majburiy.
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://dtm-test.onrender.com',
    cast=_csv,
)


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


# Render bitta DATABASE_URL beradi; lokalda alohida DB_* o'zgaruvchilar ishlatiladi.
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
            'CONN_MAX_AGE': 600,
        }
    }



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# ---------------------------------------------------------------------------
# Ko'p tillilik: o'zbekcha (asosiy), ruscha, inglizcha.
#
# Kontent (fan/mavzu/savol/tarif nomlari) modelda alohida ustunlarda
# saqlanadi — `common.i18n` ga qarang. Bu yerdagi sozlama admin paneli va
# Django xabarlariga tegishli.
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'uz'

LANGUAGES = [
    ('uz', "O'zbekcha"),
    ('ru', 'Русский'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Kunlik/haftalik reyting va streak chegaralari mahalliy yarim tunda almashishi kerak.
TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Django 5.1+ da STATICFILES_STORAGE olib tashlangan — STORAGES ishlatiladi.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# Xavfsizlik. Bu sozlamalar faqat DEBUG=False bo'lganda (ya'ni prodda) yoqiladi,
# aks holda lokal http://127.0.0.1 development ishlamay qoladi.
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    # Render/nginx proxy ortida original sxemani shu header bildiradi.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    SECURE_HSTS_SECONDS = 31536000  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# Celery — og'ir ishlar (e'lon tarqatish, reyting hisobi) so'rovdan tashqarida.
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
# Worker ishlamayotgan muhitda (masalan lokal) vazifalar darhol inline bajariladi.
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

# Davriy vazifalar. Ishlashi uchun beat ham kerak:
#   celery -A config beat --loglevel=info
CELERY_BEAT_SCHEDULE = {
    'expire-subscriptions-daily': {
        'task': 'billing.tasks.expire_subscriptions_task',
        # Har kuni mahalliy vaqt bilan 00:10 da.
        'schedule': crontab(hour=0, minute=10),
    },
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Himoyaning ikkinchi qatlami: `permission_classes` yozishni unutgan view
    # ochiq qolib ketmasin.
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsPagination",
    # Kodda 96 ta @extend_schema drf_spectacular uchun yozilgan.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "common.throttles.AnonBurstRateThrottle",
        "common.throttles.SustainedUserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        'sustained': '1000/day',
        "anon_burst": "10/min",
        "user_burst": "30/min",
        "burst": "60/min",
        "otp_request": "5/min",
        "subscription_request": "20/min",
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'TestYourself API',
    'DESCRIPTION': 'TestYourself platformasi API hujjatlari',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}


# Kodda 80+ `logger.*` chaqiruvi bor; konfiguratsiyasiz ular prodda yo'qoladi.
LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
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
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


UNFOLD = {
    "SITE_TITLE": "TestYourself Admin",
    "SITE_HEADER": "TestYourself",
    "SITE_SUBHEADER": "TestYourself boshqaruv paneli",
    "SITE_URL": "/",
    "SITE_SYMBOL": "school",
    "BORDER_RADIUS": "16px",
    "THEME": "dark",
    "SITE_LOGO": {
        "light": "/static/images/logo.png",
        "dark": "/static/images/logo.png",
    },
    "STYLES": {
        "css": [
            lambda request: """
                html body div.flex.items-center.gap-4 img.unfold-logo,
                html body .unfold-sidebar header img,
                html body a[href="/admin/"] img {
                    width: 70px !important;
                    height: 70px !important;
                    object-fit: cover !important;
                    border-radius: 50% !important;
                    border: 3px solid #10b981 !important;
                    box-shadow: 0 0 15px rgba(16, 185, 129, 0.4) !important;
                    margin: 15px auto !important;
                    display: block !important;
                }
                html body div.flex.items-center.gap-4 .material-symbols-outlined {
                    display: none !important;
                }
                html body main .grid > div,
                html body main div[class*="shadow"] {
                    background-color: #1a2333 !important;
                    border: 2px solid #2e3b52 !important;
                    border-radius: 20px !important;
                    padding: 24px !important;
                    margin-bottom: 30px !important;
                    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3) !important;
                }
                html body main .grid > div table,
                html body main .grid > div div[class*="border-b"] {
                    background: #151c2c !important;
                    border-radius: 12px !important;
                    border: 1px solid #243146 !important;
                }
                html body div[class*="login"] img,
                html body .unfold-login-box img {
                    width: 130px !important;
                    height: 130px !important;
                    border-radius: 50% !important;
                    border: 4px solid #10b981 !important;
                    box-shadow: 0 0 25px rgba(16, 185, 129, 0.5) !important;
                    margin: 0 auto 30px auto !important;
                }
                html body .unfold-sidebar {
                    background-color: #0f141c !important;
                    border-right: 1px solid #1e293b !important;
                }
                html .unfold-sidebar-section-title {
                    color: #10b981 !important;
                    font-weight: 700 !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                    border-left: 3px solid #10b981 !important;
                    padding-left: 10px !important;
                }
            """
        ],
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Asosiy",
                "separator": True,
                "items": [
                    {"title": "Bosh sahifa", "icon": "space_dashboard", "link": "/admin/"},
                ],
            },
            {
                "title": "Foydalanuvchilar (Account)",
                "separator": True,
                "collapsible": False,
                "items": [
                    {"title": "Foydalanuvchilar", "icon": "group", "link": "/admin/account/user/"},
                ],
            },
            {
                "title": "Fanlar bazasi (Catalog)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Fanlar", "icon": "menu_book", "link": "/admin/catalog/subject/"},
                    {"title": "Mavzular", "icon": "topic", "link": "/admin/catalog/topic/"},
                    {"title": "Savollar", "icon": "quiz", "link": "/admin/catalog/question/"},
                ],
            },
            {
                "title": "Test jarayoni (Testengine)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Test sessiyalari", "icon": "assignment", "link": "/admin/testengine/testsession/"},
                    {"title": "Javoblar", "icon": "fact_check", "link": "/admin/testengine/answer/"},
                    {"title": "Natijalar", "icon": "leaderboard", "link": "/admin/testengine/testresult/"},
                ],
            },
            {
                "title": "Taraqqiyot (Progress)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Takrorlash kartalari", "icon": "style", "link": "/admin/progress/reviewcard/"},
                    {"title": "Streaklar", "icon": "local_fire_department", "link": "/admin/progress/streak/"},
                    {"title": "XP tranzaksiyalari", "icon": "military_tech", "link": "/admin/progress/xptransaction/"},
                ],
            },
            {
                "title": "Obuna va to'lovlar (Billing)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Tarif rejalari", "icon": "sell", "link": "/admin/billing/plan/"},
                    {"title": "Obunalar", "icon": "card_membership", "link": "/admin/billing/subscription/"},
                    {"title": "To'lovlar", "icon": "payments", "link": "/admin/billing/payment/"},
                ],
            },
            {
                "title": "Bildirishnomalar (Notifications)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Xabarnomalar jurnali", "icon": "notifications", "link": "/admin/notifications/notificationlog/"},
                    {"title": "E'lonlar jadvali", "icon": "announcement", "link": "/admin/notifications/announcement/"},
                ],
            },
            {
                "title": "Reyting tizimi (Rating)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Reytinglar", "icon": "star", "link": "/admin/rating/rating/"},
                    {"title": "Reyting tarixlari", "icon": "history", "link": "/admin/rating/ratinghistory/"},
                    {"title": "Mavzu reytinglari", "icon": "grade", "link": "/admin/rating/topicrating/"},
                    {"title": "Fan reytinglari", "icon": "assessment", "link": "/admin/rating/subjectrating/"},
                    {"title": "Leaderboard", "icon": "leaderboard", "link": "/admin/rating/leaderboard/"},
                ],
            },
            {
                "title": "Mentor Dashboard (Dashboard)",
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": "Mentor-Talaba bog'lanishi", "icon": "people", "link": "/admin/dashboard/mentorstudent/"},
                    {"title": "Ogohlantirishlar", "icon": "warning", "link": "/admin/dashboard/mentoralert/"},
                    {"title": "Analytics Xulosa", "icon": "analytics", "link": "/admin/dashboard/analyticssummary/"},
                    {"title": "Dashboard Kirish Logi", "icon": "login", "link": "/admin/dashboard/dashboardaccess/"},
                ],
            },
        ],
    },
}