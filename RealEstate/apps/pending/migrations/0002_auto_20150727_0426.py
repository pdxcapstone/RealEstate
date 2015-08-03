# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pending', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendinghomebuyer',
            name='first_name',
            field=models.CharField(default='f', max_length=30, verbose_name=b'First Name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pendinghomebuyer',
            name='last_name',
            field=models.CharField(default='l', max_length=30, verbose_name=b'Last Name'),
            preserve_default=False,
        ),
    ]
