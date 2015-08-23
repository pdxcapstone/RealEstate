# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import RealEstate.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20150727_0426'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_confirmation_token',
            field=models.CharField(verbose_name=b'Email Confirmation Token', null=True, max_length=64, editable=False),
        ),
        migrations.AddField(
            model_name='user',
            name='email_confirmed',
            field=models.BooleanField(default=False, help_text=b'Designates if this user has confirmed their email address or not.', verbose_name=b'Active'),
        ),
    ]
