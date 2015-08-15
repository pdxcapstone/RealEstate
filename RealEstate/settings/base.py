"""
Django settings for RealEstate project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/

This file contains settings that are common to both dev and production
environments.  Dont run the app with this settings file directly, use
either dev.py or prod.py.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import datetime
from os.path import abspath, dirname

BASE_DIR = dirname(dirname(dirname(abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(&ezozkvk9p^g(s#%01)8rsdk!vj)owrrmni&hq#%$qt!dq+(k'

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'core.User'

APP_NAME = 'Real Estate App'

PASSWORD_COMMON_SEQUENCES = []

INSTALLED_APPS = (
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'passwords',

    # Third party apps
    'django_extensions',
    'bootstrap3',

    # Real Estate apps
    'RealEstate.apps.core',
    'RealEstate.apps.pending',
    'RealEstate.apps.api'
)

# REST API settings

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
}

JWT_AUTH = {
    'JWT_PAYLOAD_HANDLER':
    'RealEstate.apps.api.utils.jwt_payload_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
    'RealEstate.apps.api.utils.jwt_response_payload_handler',

    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=3000),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(seconds=3000),
    'JWT_SECRET_KEY': SECRET_KEY,
}

# End REST API settings

LOGIN_URL = 'signup'
LOGIN_REDIRECT_URL = 'dashboard'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'RealEstate.urls'

TEMPLATES = [ {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'RealEstate', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'RealEstate.apps.core.context_processors.app_name',
                'RealEstate.apps.core.context_processors.async_login_form',
                'RealEstate.apps.core.context_processors.navbar',
            ],
        },
    },
]

WSGI_APPLICATION = 'RealEstate.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
