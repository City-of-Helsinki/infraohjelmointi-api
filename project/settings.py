"""
Django settings for infraohjelmointi project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from os import path
import os
from pathlib import Path
import dj_database_url
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# asyncronous application for django event stream
ASGI_APPLICATION = "project.asgi.application"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
    DATABASE_URL=(str, "sqlite:////tmp/my-tmp-sqlite.db"),
    DJANGO_ADMIN_LANGUAGE=(str, "fi"),
    ALLOWED_CORS_ORIGINS=(list, ["http://localhost:4000", "http://localhost:3000"]),
    STATIC_ROOT=(str, BASE_DIR / "static"),
    STATIC_URL=(str, "/static/"),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    HELSINKI_TUNNISTUS_ISSUER=(
        str,
        "https://tunnistus.test.hel.ninja/auth/realms/helsinki-tunnistus",
    ),
    HELSINKI_TUNNISTUS_AUDIENCE=(str, "infraohjelmointi-api-dev"),
    HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED=(bool, False),
    SOCIAL_AUTH_TUNNISTAMO_SCOPE=(str, "ad_group"),
)

if path.exists(".env"):
    environ.Env().read_env(".env")

DEBUG = env("DEBUG")
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL")
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


INSTALLED_APPS = [
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # disable Django’s static file handling during development so that whitenoise can take over
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "simple_history",
    "overrides",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "drf_standardized_errors",
    "channels",
    "django_eventstream",
    "social_django",
    "infraohjelmointi_api",
]

# Application definition
AUTH_USER_MODEL = "infraohjelmointi_api.User"

AUTHENTICATION_BACKENDS = [
    "helusers.tunnistamo_oidc.TunnistamoOIDCAuth",
    "django.contrib.auth.backends.ModelBackend",
]

SOCIAL_AUTH_TUNNISTAMO_SCOPE = env("SOCIAL_AUTH_TUNNISTAMO_SCOPE")
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoiseMiddleware should be above all and just below SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_grip.GripMiddleware",
]

ROOT_URLCONF = "project.urls"

CORS_ALLOWED_ORIGINS = env("ALLOWED_CORS_ORIGINS")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL"))}

HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED = env("HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED")

# These settings specify which authentication server(s) are trusted
# to send back channel logout requests.
OIDC_API_TOKEN_AUTH = {
    # Who we trust to sign the logout tokens. The library will request
    # the public signature keys from standard locations below this URL.
    # Multiple issuers are supported, so this setting can also be a list
    # of strings. Default is https://tunnistamo.hel.fi.
    "ISSUER": env("HELSINKI_TUNNISTUS_ISSUER"),
    # Audience that must be present in the logout token for it to
    # be accepted. Value must be agreed between your SSO service
    # and your application instance. Essentially this allows your
    # application to know that the token is meant to be used with
    # it. Multiple acceptable audiences are supported, so this
    # setting can also be a list of strings. This setting is required.
    "AUDIENCE": env("HELSINKI_TUNNISTUS_AUDIENCE"),
}

from helusers.defaults import SOCIAL_AUTH_PIPELINE


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = env("DJANGO_ADMIN_LANGUAGE")

TIME_ZONE = "Europe/Helsinki"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


STATIC_URL = env("STATIC_URL")
STATIC_ROOT = env("STATIC_ROOT")


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("helusers.oidc.ApiTokenAuthentication",),
}

DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": False}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s %(pathname)s:%(lineno)d %(message)s",
            "datefmt": "[%d/%b/%Y %H:%M:%S]",
            "()": "project.customlogging.ColoredFormatter",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL"),
    },
    "loggers": {
        "infraohjelmointi_api": {
            "handlers": ["console"],
            "level": 1,
            "propagate": False,
        },
        # "helusers._oidc_auth_impl": {
        #     "handlers": ["console"],
        #     "level": 1,
        #     "propagate": False,
        # },
    },
}


# Caching framework defaults

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": 60 * 60 * 2,  # 2 hour timeout default
        "OPTIONS": {"MAX_ENTRIES": 3000},
    }
}
