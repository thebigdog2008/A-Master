from copy import deepcopy

from django.utils.log import DEFAULT_LOGGING

import sentry_sdk
from kombu import Exchange, Queue  # NOQA
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from config.settings.base import *  # noqa: F403

DEBUG = False

ADMINS = env.json("ADMINS")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SECRET_KEY = env("SECRET_KEY")
HASHID_FIELD_SALT = env("HASHID_FIELD_SALT")


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
# --------------------------------------------------------------------------

DATABASES = {
    "default": env.db(),
}


# Template
# --------------------------------------------------------------------------

TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    ),
]


# --------------------------------------------------------------------------

USE_COMPRESSOR = env.bool("USE_COMPRESSOR")
USE_CLOUDFRONT = env.bool("USE_CLOUDFRONT")
USE_HTTPS = env.bool("USE_HTTPS")
if USE_HTTPS:
    LETSENCRYPT_DIR = env("LETSENCRYPT_DIR", default="/opt/letsencrypt/")


# Storage configurations
# --------------------------------------------------------------------------

AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_AUTO_CREATE_BUCKET = True


AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = USE_HTTPS


if USE_CLOUDFRONT:
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN")
else:
    AWS_S3_CUSTOM_DOMAIN = "{0}.s3.amazonaws.com".format(AWS_STORAGE_BUCKET_NAME)

# STATIC_URL = 'http{0}://{1}/static/'.format('s' if USE_HTTPS else '', AWS_S3_CUSTOM_DOMAIN)
# MEDIA_URL = 'http{0}://{1}/media/'.format('s' if USE_HTTPS else '', AWS_S3_CUSTOM_DOMAIN)
# MEDIA_URL = "/media/"
# STATIC_URL = '/static/'
# STATIC_ROOT  = os.path.join(BASE_DIR, "static")
# DEFAULT_FILE_STORAGE = 'config.settings.s3utils.MediaRootS3BotoStorage'
# STATICFILES_STORAGE = 'config.settings.s3utils.StaticRootS3BotoStorage'


# Compressor & Cloudfront settings
# --------------------------------------------------------------------------

if USE_CLOUDFRONT or USE_COMPRESSOR:
    AWS_HEADERS = {"Cache-Control": str("public, max-age=604800")}

if USE_COMPRESSOR:
    INSTALLED_APPS += ("compressor",)
    STATICFILES_FINDERS += ("compressor.finders.CompressorFinder",)

    # See: http://django_compressor.readthedocs.org/en/latest/settings/#django.conf.settings.COMPRESS_ENABLED
    COMPRESS_ENABLED = True

    COMPRESS_STORAGE = STATICFILES_STORAGE

    # See: http://django-compressor.readthedocs.org/en/latest/settings/#django.conf.settings.COMPRESS_CSS_HASHING_METHOD
    COMPRESS_CSS_HASHING_METHOD = "content"

    COMPRESS_CSS_FILTERS = (
        "config.settings.abs_compress.CustomCssAbsoluteFilter",
        "compressor.filters.cssmin.CSSMinFilter",
    )

    COMPRESS_OFFLINE = True
    COMPRESS_OUTPUT_DIR = "cache"
    COMPRESS_CACHE_BACKEND = "locmem"


# Email settings
# --------------------------------------------------------------------------

# EMAIL_CONFIG = env.email()
# vars().update(EMAIL_CONFIG)

SERVER_EMAIL_SIGNATURE = env("SERVER_EMAIL_SIGNATURE", default="realtorx".capitalize())
DEFAULT_FROM_EMAIL = SERVER_EMAIL = SERVER_EMAIL_SIGNATURE + " <{0}>".format(
    env("SERVER_EMAIL")
)


# Google analytics settings
# --------------------------------------------------------------------------

GOOGLE_ANALYTICS_PROPERTY_ID = env("GA_PROPERTY_ID", default="")
GA_ENABLED = bool(GOOGLE_ANALYTICS_PROPERTY_ID)


# if CELERY_ENABLED:
#     # Celery configurations
#     # http://docs.celeryproject.org/en/latest/configuration.html
#     # --------------------------------------------------------------------------
#
#     CELERY_BROKER_URL = env('CELERY_BROKER_URL')
#
#     CELERY_TASK_DEFAULT_QUEUE = 'realtorx-celery-queue'
#     CELERY_TASK_DEFAULT_EXCHANGE = 'realtorx-exchange'
#     CELERY_TASK_DEFAULT_ROUTING_KEY = 'celery.realtorx'
#     CELERY_TASK_QUEUES = (
#         Queue(
#             CELERY_TASK_DEFAULT_QUEUE,
#             Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
#             routing_key=CELERY_TASK_DEFAULT_ROUTING_KEY,
#         ),
#     )

if CELERY_ENABLED:
    # Celery configurations
    # http://docs.celeryproject.org/en/latest/configuration.html
    # --------------------------------------------------------------------------

    CELERY_TASK_BROKER_URL = env("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND_URL")

    if "redis" in CELERY_TASK_BROKER_URL:
        CELERY_BROKER_TRANSPORT_OPTIONS = {
            "visibility_timeout": 60 * 60 * 24 * 9,
        }
        # CELERY_TASK_DEFAULT_QUEUE = 'realtorx-celery-queue'
        # CELERY_TASK_DEFAULT_EXCHANGE = 'realtorx-exchange'
        # CELERY_TASK_DEFAULT_ROUTING_KEY = 'celery.realtorx'
        # CELERY_TASK_QUEUES = (
        #     Queue(
        #         CELERY_TASK_DEFAULT_QUEUE,
        #         Exchange(CELERY_TASK_DEFAULT_EXCHANGE),
        #         routing_key=CELERY_TASK_DEFAULT_ROUTING_KEY,
        #     ),
        # )

# FCM Push Notifications configuration
# ------------------------------------

FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"] = env("FCM_SERVER_KEY", default=None)


# Firebase Admin Chat SDK config
# ------------------------------

FIREBASE_PROJECT_ID = env("FIREBASE_PROJECT_ID")
FIREBASE_DATABASE = env("FIREBASE_DATABASE")
FIREBASE_BRANCH = env("FIREBASE_BRANCH")
FIREBASE_SERVICE_ACCOUNT_CLIENT_EMAIL = env("FIREBASE_SERVICE_ACCOUNT_CLIENT_EMAIL")
FIREBASE_SERVICE_ACCOUNT_PRIVATE_KEY = env("FIREBASE_SERVICE_ACCOUNT_PRIVATE_KEY")


# Firebase webhooks
# ------------------------
FIREBASE_WEBHOOK_API_KEY = env("FIREBASE_WEBHOOK_API_KEY", default="")


# Sentry config
# -------------

SENTRY_DSN = env("SENTRY_DSN", default="")
SENTRY_ENABLED = True if SENTRY_DSN else False

if SENTRY_ENABLED:
    sentry_sdk.init(
        SENTRY_DSN,
        traces_sample_rate=0.2,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment=APP_ENVIRONMENT,
    )

    logging_dict = deepcopy(DEFAULT_LOGGING)
    logging_dict["loggers"]["django"]["handlers"] = ["console"]

    LOGGING = logging_dict


CACHES["default"]["BACKEND"] = "django_redis.cache.RedisCache"
CACHES["default"]["LOCATION"] = env("REDIS_URL", default="redis://127.0.0.1:6379/1")
# Imagekit RedisCache
# CACHES['imagekit']['BACKEND'] = 'django_redis.cache.RedisCache'
# CACHES['imagekit']['LOCATION'] = env('REDIS_URL')  # todo: use env variable

# Google OAuth2 configuration
# --------------------------------------------------------------------------
GOOGLE_CLIENT_SECRETS = {
    "web": {
        "client_id": env("GOOGLE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": env("GOOGLE_CLIENT_SECRET"),
    },
}
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]


# Microsoft OAuth2 configuration
# --------------------------------------------------------------------------
MICROSOFT_CLIENT_ID = env("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = env("MICROSOFT_CLIENT_SECRET")
MICROSOFT_SCOPES = ["offline_access", "user.read", "calendars.readwrite"]


# UpTimeBot settings
# ------------------
UPTIMEBOT_TOKEN = env("UPTIMEBOT_TOKEN")


# Social Auth keys
# --------------------
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")

SOCIAL_AUTH_FACEBOOK_KEY = env("SOCIAL_AUTH_FACEBOOK_KEY")
SOCIAL_AUTH_FACEBOOK_SECRET = env("SOCIAL_AUTH_FACEBOOK_SECRET")

SOCIAL_AUTH_APPLE_ID_CLIENT = env("SOCIAL_AUTH_APPLE_ID_CLIENT")
SOCIAL_AUTH_APPLE_ID_TEAM = env("SOCIAL_AUTH_APPLE_ID_TEAM")
SOCIAL_AUTH_APPLE_ID_KEY = env("SOCIAL_AUTH_APPLE_ID_KEY")
try:
    import base64

    apple_id_secret_encoded = env("SOCIAL_AUTH_APPLE_ID_SECRET_base64")
    if apple_id_secret_encoded:
        SOCIAL_AUTH_APPLE_ID_SECRET = base64.b64decode(apple_id_secret_encoded)
except Exception as ex:  # NOQA
    print(f"Unable to load SOCIAL_AUTH_APPLE_ID_SECRET: {ex}")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "400_log_file": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "500_log_file": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "list_hub_log_file": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "validation_log_file": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propogate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "400_logs": {
            "handlers": ["400_log_file"],
            "level": "DEBUG",
            "propogate": True,
        },
        "500_logs": {
            "handlers": ["500_log_file"],
            "level": "DEBUG",
            "propogate": True,
        },
        "django.list_hub": {
            "handlers": ["list_hub_log_file"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.validation_log": {
            "handlers": ["validation_log_file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
