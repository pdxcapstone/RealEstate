# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import RealEstate.apps.pending.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingCouple',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('realtor', models.ForeignKey(verbose_name=b'Realtor', to='core.Realtor')),
            ],
            options={
                'ordering': ['realtor'],
                'verbose_name': 'Pending Couple',
                'verbose_name_plural': 'Pending Couples',
            },
        ),
        migrations.CreateModel(
            name='PendingHomebuyer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=75, verbose_name=b'Email')),
                ('registration_token', models.CharField(default=RealEstate.apps.pending.models._generate_registration_token, verbose_name=b'Registration Token', unique=True, max_length=64, editable=False)),
                ('pending_couple', models.ForeignKey(verbose_name=b'Pending Couple', to='pending.PendingCouple')),
            ],
            options={
                'ordering': ['email'],
                'verbose_name': 'Pending Homebuyer',
                'verbose_name_plural': 'Pending Homebuyers',
            },
        ),
    ]
