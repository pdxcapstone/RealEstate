"""
Create a superuser if it does not already exist in the database.

python manage.py runscript superuser
"""
import sys
from django.contrib.auth import get_user_model

USERNAME = 'admin'
PASSWORD = 'admin'
EMAIL = 'admin@admin.com'


def run():
    User = get_user_model()
    login_info = "({username}:{password})".format(
        username=USERNAME, password=PASSWORD)
    if User.objects.filter(username=USERNAME).exists():
        print "Superuser already exists {}".format(login_info)
        sys.exit(1)
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print "Superuser created {}".format(login_info)
