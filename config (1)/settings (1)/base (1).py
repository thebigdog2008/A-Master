from pathlib import Path

import environ

# Build paths inside the project like this: root(...)
from corsheaders.defaults import default_headers
from kombu import Exchange, Queue

env = environ.Env()
environ.Env.read_env()

root = environ.Path(__file__) - 3
apps_root = root.path("realtorx")

BASE_DIR = root()

APP_NAME = env("APP_NAME", default=" ")
APP_ENVIRONMENT = env("APP_ENVIRONMENT", default="Production")

# Base configurations
# --------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "custom_auth.ApplicationUser"

AUTHENTICATION_BACKENDS = (
    "realtorx.registrations.auth_backends.apple.SwitchableAppleIdAuthBackend",
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "realtorx.custom_auth.auth_backends.model_backend.CustomModelBackend",
)

# Application definition
# --------------------------------------------------------------------------

DJANGO_APPS = [
    "django_crontab",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.gis",
    "django.contrib.humanize",
    "drf_api_logger",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_secure_token",
    "fcm_django",
    "mapwidgets",
    "corsheaders",
    "timezone_field",
    "django_filters",
    "fsm_admin",
    "phonenumber_field",
    "social_django",
    "drf_yasg2",
    "import_export",
    "rangefilter",
]

LOCAL_APPS = [
    "realtorx.mailing",
    "realtorx.taskapp",
    "realtorx.photo",
    "realtorx.attachments",
    "realtorx.agencies",
    "realtorx.custom_auth",
    "realtorx.following",
    "realtorx.houses",
    "realtorx.registrations",
    "realtorx.cities",
    "realtorx.statistics",
    "realtorx.ui",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware configurations
# --------------------------------------------------------------------------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "realtorx.custom_auth.current_user.CurrentUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.settings.middleware.Log400Response",
    "config.settings.middleware.Log500Response",
    "drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware",
]

# Template configurations
# --------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            root("realtorx", "templates"),
        ],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "realtorx.context_processors.google_analytics",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

# Fixture configurations
# --------------------------------------------------------------------------

FIXTURE_DIRS = [
    root("realtorx", "fixtures"),
]

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators
# --------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
# --------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# --------------------------------------------------------------------------

# STATIC_URL = '/static/'
# STATIC_ROOT = root('static')

# STATICFILES_FINDERS = (
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#     'django.contrib.staticfiles.finders.FileSystemFinder',
# )

# STATICFILES_DIRS = [
#     root('realtorx', 'assets'),
# ]

# MEDIA_URL = '/media/'
STATIC_URL = "/static/"
STATIC_ROOT = "/static"


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
)

STATICFILES_DIRS = [root("static")]


MEDIA_ROOT = root("media")

CELERY_ENABLED = env.bool("CELERY_ENABLED", default=True)
# if CELERY_ENABLED:
#     # Celery configuration
#     # --------------------------------------------------------------------------
#
#     CELERY_ACCEPT_CONTENT = ['json']
#     CELERY_TASK_SERIALIZER = 'json'
#     CELERY_TASK_IGNORE_RESULT = True

if CELERY_ENABLED:
    # Celery configuration
    # --------------------------------------------------------------------------

    CELERY_ACCEPT_CONTENT = ["json"]  # todo: pickle is unsafe & deprecated. use json
    CELERY_TASK_SERIALIZER = "json"
    CELERY_TASK_RESULT_SERIALIZER = "json"

    CELERY_TASK_IGNORE_RESULT = True

    CELERY_TASK_DEFAULT_QUEUE = "realtorx-celery-queue"
    CELERY_TASK_DEFAULT_EXCHANGE = "realtorx-exchange"
    CELERY_TASK_DEFAULT_ROUTING_KEY = CELERY_TASK_DEFAULT_QUEUE
    CELERY_NOTIFICATION_QUEUE = "realtorx-celery-notifications-queue"
    CELERY_LIST_HUB_QUEUE = "realtorx-celery-list-hub-queue"
    CELERY_LIST_HUB_QUEUE_V2 = "realtorx-celery-list-hub-queue-v2"

    CELERY_TASK_QUEUES = (
        Queue(
            CELERY_TASK_DEFAULT_QUEUE,
            Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
            routing_key=CELERY_TASK_DEFAULT_QUEUE,
        ),
        Queue(
            CELERY_NOTIFICATION_QUEUE,
            Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
            routing_key=CELERY_NOTIFICATION_QUEUE,
        ),
        Queue(
            CELERY_LIST_HUB_QUEUE,
            Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
            routing_key=CELERY_LIST_HUB_QUEUE,
        ),
        Queue(
            CELERY_LIST_HUB_QUEUE_V2,
            Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
            routing_key=CELERY_LIST_HUB_QUEUE_V2,
        ),
    )

    CELERY_TASK_ROUTES = {}

    TASK_ROUTES_SETTINGS = {
        CELERY_NOTIFICATION_QUEUE: [
            "realtorx.mailing.tasks.*",
            "realtorx.statistics.tasks.create_daily_statistics_report",
            "realtorx.statistics.tasks.send_report_email",
            "realtorx.statistics.tasks.create_30_day_statistics_report",
        ],
        CELERY_LIST_HUB_QUEUE: [
            "realtorx.crm.views.get_list_hub_data",
            "realtorx.crm.tasks.fetch_listhub_listings_v3",
            "realtorx.crm.tasks.fetch_listhub_listings_daily",
            "realtorx.crm.tasks.collect_listhub_listings",
            "realtorx.crm.tasks.process_listing",
            "realtorx.crm.tasks.send_mixpanel_event",
        ],
        CELERY_LIST_HUB_QUEUE_V2: [
            "realtorx.crm.tasks.fetch_previous_listings",
            "realtorx.crm.tasks.collect_listhub_listings_v2",
            "realtorx.crm.tasks.process_listing_v2",
        ],
    }
    for queue_key, tasks_names in list(TASK_ROUTES_SETTINGS.items()):
        for task_name in tasks_names:
            CELERY_TASK_ROUTES[task_name] = {
                "queue": queue_key,
                "routing_key": queue_key,
            }

    CELERY_ACKS_LATE = True
    CELERY_TASK_REJECT_ON_WORKER_LOST = True
    CELERYD_PREFETCH_MULTIPLIER = 1  # default is 4 but we are setting to 1 so that on restarting the server we do not have extra prefetched tasks.

    # Use CELERY_ANNOTATIONS setting to override the defaualt config for certain tasks
    # # CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}} # overides the default rate_limit behaviour
    # class MyAnnotate:

    #     def annotate(self, task):
    #         if task.name.startswith('tasks.'):
    #             return {'rate_limit': '10/s'}

    # CELERY_ANNOTATIONS = (MyAnnotate(), {other,})

# Django mailing configuration
# --------------------------------------------------------------------------

if CELERY_ENABLED:
    TEMPLATED_EMAIL_BACKEND = "realtorx.mailing.backends.AsyncTemplateBackend"
    MAILING_USE_CELERY = True

TEMPLATED_EMAIL_TEMPLATE_DIR = "email/"
TEMPLATED_EMAIL_FILE_EXTENSION = "html"

# Rest framework configuration
# http://www.django-rest-framework.org/api-guide/settings/
# --------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "PAGE_SIZE": 10,
    "DEFAULT_PAGINATION_CLASS": "unicef_restlib.pagination.DynamicPageNumberPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "drf_secure_token.authentication.SecureTokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}

# Social Auth configurations
# --------------------------

SOCIAL_AUTH_POSTGRES_JSONFIELD = True

# Apple specific

SOCIAL_AUTH_APPLE_ID_SCOPE = ["email"]

# Facebook specific

FACEBOOK_MIN_AGE_RESTRICTION = None

# Facebook doesn't return the exact size asked for, it returns the closest dimension picture available with them.
FACEBOOK_PROFILE_PIC_TARGET_SIZE = 1500
# remove `.height()` part if non-squared picture is required
FB_PROFILE_PIC_FIELD = "picture.width({0}).height({0})".format(
    FACEBOOK_PROFILE_PIC_TARGET_SIZE
)

SOCIAL_AUTH_FACEBOOK_SCOPE = [
    "email",
    "public_profile",
    "user_birthday",
    "user_location",
    "user_photos",
]

SOCIAL_AUTH_FACEBOOK_USER_FIELDS = ["username", "email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    "fields": "id,email,name,first_name,last_name,age_range,birthday,"
    f"hometown,location,address,verified,timezone,locale,languages,{FB_PROFILE_PIC_FIELD}",
}

FACEBOOK_USE_BUSINESS_TOKEN = env.bool("FACEBOOK_USE_BUSINESS_TOKEN", default=False)
if FACEBOOK_USE_BUSINESS_TOKEN:
    SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS["fields"] += ",token_for_business"

SOCIAL_AUTH_CLEAN_USERNAME_FUNCTION = "realtorx.custom_auth.utils.clean_username"

SOCIAL_AUTH_PROTECTED_USER_FIELDS = ("email",)
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "realtorx.custom_auth.auth_pipeline.user_details_custom",
    "realtorx.custom_auth.auth_pipeline.fetch_profile_picture",
)

# Twilio configurations
# --------------------------------------------------------------------------

TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default=" ")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default=" ")
TWILIO_PHONE = env("TWILIO_PHONE", default="")
TWILIO_VERIFY_SERVICE = env("TWILIO_VERIFY_SERVICE", default="")

# Firebase settings
# -----------------

FIREBASE_PROJECT_ID = ""
FIREBASE_DATABASE = ""
FIREBASE_SERVICE_ACCOUNT_CLIENT_EMAIL = ""
FIREBASE_SERVICE_ACCOUNT_PRIVATE_KEY = ""

FIREBASE_WEBHOOK_API_KEY = ""

# FCM Push Notifications configuration
# ------------------------------------

FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": None,
    # true if you want to have only one active device per registered user at a time
    "ONE_DEVICE_PER_USER": False,
    # devices to which notifications cannot be sent, are deleted upon receiving error response from FCM
    "DELETE_INACTIVE_DEVICES": False,
}

# FCM Push Notifications configuration
# ------------------------------------

FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"] = env("FCM_SERVER_KEY", default=None)

# Django cache settings
# ------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "imagekit": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "imagekit_cache",
        "OPTIONS": {
            "MAX_ENTRIES": 10
            ** 20,  # there is no ability to dodge argument; any other case resulting to 300
        },
    },
}

# Imagekit cache settings
# ------------------------------------

IMAGEKIT_CACHE_BACKEND = "imagekit"
IMAGEKIT_CACHE_TIMEOUT = 60 * 60 * 24 * 365 * 100  # 100 years; None don't work
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = "realtorx.utils.imagekit.SafeCacheFileBackend"
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = "imagekit.cachefiles.strategies.Optimistic"

# Django admin map widget
# -----------------------

MAP_WIDGETS = {
    "GOOGLE_MAP_API_KEY": env("GOOGLE_MAP_API_KEY", default=""),
}

# CORS headers settings
# ---------------------
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-Token",
]
CORS_EXPOSE_HEADERS = ["X-Token"]

# DRF Secure Token configurations
# -------------------------------

MUTABLE_PERIOD = 60 * 60 * 24 * 10  # 10 days
TOKEN_AGE = 60 * 60 * 24 * 183  # 183 days

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "api_key": {"type": "apiKey", "in": "header", "name": "Authorization"}
    },
}

# parameters values
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# set agent interest notification flag
AGENT_INTEREST_NOTIFICATION_FLAG = True

# set seller landlord interest notification flag
SELLER_LANDLORD_INTEREST_ALERT = True

# set daily check or delete amazing listing
DAILY_CHECK_OR_DELETE_AMAZING_LISTING = True
NUMBER_OF_DAYS = 7

# cronjob
CRONJOBS = [
    (
        "*/1 14-23,0-1 * * * ",
        "realtorx.following.tasks.send_reminder_push",
        ">>" + "/home/ubuntu/realtorx/push_reminder.log",
    )
]

DRF_API_LOGGER_DATABASE = True

# request body data uploading size
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600

IMPORT_EXPORT_USE_TRANSACTIONS = True

# List hub Credentials
CLIENT_ID = env("CLIENT_ID", default="")
CLIENT_SECRET = env("CLIENT_SECRET", default="")
LIST_HUB_THREADS = env("LIST_HUB_THREADS", default=1)

# List hub reporting flag
LIST_HUB_REPORTING_FLAG = True

# Default id and email for test email templates.
TEST_DEFAULT_EMAIL = "dev@sandboxf8b9eb29c9db4122a6dd3850ab760547.mailgun.org"
TEST_DEFAULT_EMAIL_RECIPIENT = "agentloop-test-mail@protonmail.com"

EMAILS_ENABLED = env.bool("EMAILS_ENABLED", default=False)

# List of email addresses allowed to receive test emails if EMAILS_ENABLED is False
EMAIL_ALLOWED_ADDRESSES = env.list("EMAIL_ALLOWED_ADDRESSES", default=[])

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY", default="")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Email addresses to BCC all emails to
EMAIL_BCC = env.list("EMAIL_BCC", default=[])

LOG_FOLDER = Path(env("LOG_FOLDER", default="/data/realtorx-logs"))

# GDAL_LIBRARY_PATH = '/opt/homebrew/lib/libgdal.dylib'
# GEOS_LIBRARY_PATH = '/opt/homebrew/lib/libgeos_c.dylib'

# EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
# EMAIL_HOST = env('EMAIL_HOST', default='smtp.mailgun.org')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='agentloop@sandbox10f21b5fefe640779ecd3dec62d42fb5.mailgun.org')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='caedac6f8a190f6d75b5147ceff63d25-c76388c3-1360e893')
# EMAIL_USE_TLS = True
# EMAIL_PORT = 465

FILTER_MAX_PRICE = 250000000

APPLE_SHARED_SECRET = env("APPLE_SHARED_SECRET", default="")
ANDROID_PACKAGE_NAME = env("ANDROID_PACKAGE_NAME", default="com.realtorx")
ANDROID_PAYMENT_PRODUCT_ID = env(
    "ANDROID_PAYMENT_PRODUCT_ID", default="agentloopx_listing_credit"
)
MIXPANEL_TOKEN = env("MIXPANEL_TOKEN", default="")
MIXPANEL_PROJECT_ID = env("MIXPANEL_PROJECT_ID", default="")
MIXPANEL_SERVICE_ACCOUNT_USERNAME = env("MIXPANEL_SERVICE_ACCOUNT_USERNAME", default="")
MIXPANEL_SERVICE_ACCOUNT_PASSWORD = env("MIXPANEL_SERVICE_ACCOUNT_PASSWORD", default="")
MIXPANEL_TRACKING_ENABLED = env("MIXPANEL_TRACKING_ENABLED", default=True)

MAX_MEDIA_PHOTOS = 8
DEFAULT_FILTER_ZIPCODE_RANGE = 3
DEFAULT_FILTER_PRICE_RANGE = 0.1
