"""
Settings that are specific to a production environment.
"""
from RealEstate.settings.base import *

ALLOWED_HOSTS = ['*']

DEBUG = False
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'RealEstate',                      
        'USER': 'django',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
