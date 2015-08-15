# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import RealEstate.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20150805_0656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email_confirmation_token',
            field=models.CharField(default=RealEstate.apps.core.models._generate_email_confirmation_token, verbose_name=b'Email Confirmation Token', unique=True, max_length=64, editable=False),
        ),
    ]
