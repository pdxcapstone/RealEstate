# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoryweight',
            name='weight',
            field=models.PositiveSmallIntegerField(default=3, choices=[(1, b'Unimportant'), (2, b'Below Average'), (3, b'Average'), (4, b'Above Average'), (5, b'Important')], verbose_name=b'Weight', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='grade',
            name='score',
            field=models.PositiveSmallIntegerField(default=3, verbose_name=b'Score', choices=[(1, b'Poor'), (2, b'Below Average'), (3, b'Average'), (4, b'Above Average'), (5, b'Excellent')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True, max_length=254, verbose_name=b'Email Address', error_messages={b'unique': b'A user with this email already exists.'}),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=30, verbose_name=b'First Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=30, verbose_name=b'Last Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=20, verbose_name=b'Phone Number', validators=[django.core.validators.RegexValidator(regex=b'^[0-9-()+]{10,20}$', message=b'Please enter a valid phone number.', code=b'phone_format')]),
        ),
    ]
