# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20150805_0657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email_confirmed',
            field=models.BooleanField(default=False, help_text=b'Designates if this user has confirmed their email address or not.', verbose_name=b'Email Confirmed'),
        ),
    ]
