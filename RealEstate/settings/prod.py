"""
Settings that are specific to a production environment.
"""
from ConfigParser import RawConfigParser
from django.core.exceptions import ImproperlyConfigured
from RealEstate.settings.base import *

STATIC_ROOT = "/opt/myenv/static/"

ALLOWED_HOSTS = ['capstonedd.cs.pdx.edu']

DEBUG = False
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django',
        'USER': 'django',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '',
    }
}

PASSWORD_MIN_LENGTH = 8
PASSWORD_COMPLEXITY = {
    'LOWER': 1,
    'UPPER': 1,
    'DIGITS': 1,
}
PASSWORD_ERROR_MESSAGE = (
    u"Invalid Password.  Must be at least 8 characters, mixed case, and "
    "contain at least one digit")


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
