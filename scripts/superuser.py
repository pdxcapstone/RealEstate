"""
Create a superuser if it does not already exist in the database.

python manage.py runscript superuser
"""
import sys
from django.contrib.auth import get_user_model

EMAIL = 'admin@admin.com'
PASSWORD = 'admin'


def run():
    User = get_user_model()
    login_info = "({email}:{password})".format(email=EMAIL, password=PASSWORD)

    if User.objects.filter(email=EMAIL).exists():
        print "Superuser already exists {}".format(login_info)
        sys.exit(1)
    User.objects.create_superuser(EMAIL, PASSWORD,
                                  first_name="Admin", last_name="Admin")
    print "Superuser created {}".format(login_info)
