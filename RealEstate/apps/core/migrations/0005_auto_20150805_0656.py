# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.crypto import get_random_string, hashlib

def gen_email_token(apps, schema_editor):
    User = apps.get_model('core', 'User')
    for row in User.objects.all():
        row.email_confirmation_token = hashlib.sha256(
            get_random_string(length=64)).hexdigest()
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20150805_0656'),
    ]

    operations = [
        migrations.RunPython(
            gen_email_token, reverse_code=migrations.RunPython.noop),
    ]
