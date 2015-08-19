# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='summary',
            field=models.CharField(max_length=128, verbose_name=b'Category Name'),
        ),
    ]
