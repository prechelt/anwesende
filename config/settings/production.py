from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"] = env.db("DATABASE_URL")  # noqa F405
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405

# CACHES
# ------------------------------------------------------------------------------
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": env("REDIS_URL"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             # Mimicing memcache behavior.
#             # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
#             "IGNORE_EXCEPTIONS": True,
#         },
#     }
# }
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'the-one-and-only',
    }
}

# SECURITY  
# ------------------------------------------------------------------------------
DJANGO_HTTPS_INSIST = env.bool("DJANGO_HTTPS_INSIST")  # an 'anwesende' pseudo-setting
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
#  SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = False
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = DJANGO_HTTPS_INSIST
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = DJANGO_HTTPS_INSIST
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
SECURE_HSTS_SECONDS = 366 * 24 * 3600 if DJANGO_HTTPS_INSIST else 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = DJANGO_HTTPS_INSIST
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = DJANGO_HTTPS_INSIST
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = DJANGO_HTTPS_INSIST

# STATIC and MEDIA
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[-1]["OPTIONS"]["loaders"] = [  # type: ignore[index] # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# https://docs.djangoproject.com/en/dev/topics/logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": '/djangolog/django.log',
            "formatter": "verbose",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": '/djangolog/django-errors.log',
            "formatter": "verbose",
        },
        "file_request": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": '/djangolog/django-requests.log',
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["file_request"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "level": "ERROR",
            "handlers": ["console", "file_error"],
            "propagate": True,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    },
}
