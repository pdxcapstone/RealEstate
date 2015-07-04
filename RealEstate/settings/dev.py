"""
Settings that are specific to a dev environment.
"""
from RealEstate.settings.base import *


DEBUG = True
TEMPLATE_DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'RealEstate', 'db', 'db.sqlite3'),
    }
}
