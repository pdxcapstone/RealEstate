"""
Settings that are specific to a production environment.
"""
from RealEstate.settings.base import *


DEBUG = False
TEMPLATE_DEBUG = False

# Need to fill this in with our Postgres production settings.
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#     }
# }
