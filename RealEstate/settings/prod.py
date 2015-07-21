"""
Settings that are specific to a production environment.
"""
from configparser import RawConfigParser
from django.core.exceptions import ImproperlyConfigured
from RealEstate.settings.base import *

STATIC_ROOT = "/opt/myenv/static/"

ALLOWED_HOSTS = ['*']

DEBUG = True
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django',
        'USER': 'django',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Expects a config file in the project directory which contains private
# information that should not be stored in the repository, such as the
# host email/password.
PROJECT_CONFIG_FILE = os.path.join(BASE_DIR, 'real-estate.conf')
parser = RawConfigParser()
parser.optionxform = str
parsed_files = parser.read([PROJECT_CONFIG_FILE])

if not parsed_files:
    raise ImproperlyConfigured("Failed to parse project config file. Make "
                               "sure the file exists and is located at "
                               "{config_file}".format(
                                   config_file=PROJECT_CONFIG_FILE))

if not all([parser.has_section('email'),
            parser.has_option('email', 'email'),
            parser.has_option('email', 'password')]):
    raise ImproperlyConfigured("Config file must contain an 'email' section "
                               "with 'email' and 'password' options.")

EMAIL_HOST_USER = parser.get('email', 'email')
EMAIL_HOST_PASSWORD = parser.get('email', 'password')
