"""
Settings that are specific to a dev environment.
"""
from ConfigParser import RawConfigParser
from RealEstate.settings.base import *


DEBUG = True
TEMPLATE_DEBUG = True

DATABASE_PATH = os.path.join(BASE_DIR, 'RealEstate', 'db')
DATABASE_NAME = 'db.sqlite3'

PASSWORD_MIN_LENGTH = 1
#PASSWORD_COMPLEXITY = {}
PASSWORD_ERROR_MESSAGE = u"Invalid Password"

# Check for custom database usage.
PROJECT_CONFIG_FILE = os.path.join(BASE_DIR, 'real-estate.conf')
parser = RawConfigParser()
parser.optionxform = str
parsed_files = parser.read([PROJECT_CONFIG_FILE])
if all([parsed_files,
        parser.has_section('dev'),
        parser.has_option('dev', 'db')]):
    custom_db = parser.get('dev', 'db')
    if os.path.exists(os.path.join(DATABASE_PATH, custom_db)):
        DATABASE_NAME = custom_db

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATABASE_PATH, DATABASE_NAME)
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
