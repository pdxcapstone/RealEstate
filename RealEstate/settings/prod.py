"""
Settings that are specific to a production environment.
"""
from RealEstate.settings.base import *

STATIC_ROOT = "/opt/myenv/static/"

ALLOWED_HOSTS = ['capstonedd.cs.pdx.edu']

DEBUG = False
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django',                      
        'USER': 'postgres',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
	'PORT': '',
    }
}
