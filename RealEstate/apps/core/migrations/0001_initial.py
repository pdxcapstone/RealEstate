# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models
import RealEstate.apps.core.models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('summary', models.CharField(max_length=128, verbose_name=b'Summary')),
                ('description', models.TextField(verbose_name=b'Description', blank=True)),
            ],
            options={
                'ordering': ['summary'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='CategoryWeight',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('weight', models.PositiveSmallIntegerField(help_text=b'0-100', verbose_name=b'Weight', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('category', models.ForeignKey(verbose_name=b'Category', to='core.Category')),
            ],
            options={
                'ordering': ['category', 'homebuyer'],
                'verbose_name': 'Category Weight',
                'verbose_name_plural': 'Category Weights',
            },
        ),
        migrations.CreateModel(
            name='Couple',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'ordering': ['realtor'],
                'verbose_name': 'Couple',
                'verbose_name_plural': 'Couples',
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.PositiveSmallIntegerField(default=3, verbose_name=b'Score', choices=[(1, b'1'), (2, b'2'), (3, b'3'), (4, b'4'), (5, b'5')])),
                ('category', models.ForeignKey(verbose_name=b'Category', to='core.Category')),
            ],
            options={
                'ordering': ['homebuyer', 'house', 'category', 'score'],
                'verbose_name': 'Grade',
                'verbose_name_plural': 'Grades',
            },
        ),
        migrations.CreateModel(
            name='Homebuyer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('categories', models.ManyToManyField(to='core.Category', verbose_name=b'Categories', through='core.CategoryWeight')),
                ('couple', models.ForeignKey(verbose_name=b'Couple', to='core.Couple')),
            ],
            options={
                'ordering': ['user__username'],
                'verbose_name': 'Homebuyer',
                'verbose_name_plural': 'Homebuyers',
            },
            bases=(models.Model, RealEstate.apps.core.models.ValidateCategoryCoupleMixin),
        ),
        migrations.CreateModel(
            name='House',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nickname', models.CharField(max_length=128, verbose_name=b'Nickname')),
                ('address', models.TextField(verbose_name=b'Address', blank=True)),
                ('categories', models.ManyToManyField(to='core.Category', verbose_name=b'Categories', through='core.Grade')),
                ('couple', models.ForeignKey(verbose_name=b'Couple', to='core.Couple')),
            ],
            options={
                'ordering': ['nickname'],
                'verbose_name': 'House',
                'verbose_name_plural': 'Houses',
            },
            bases=(models.Model, RealEstate.apps.core.models.ValidateCategoryCoupleMixin),
        ),
        migrations.CreateModel(
            name='Realtor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'ordering': ['user__username'],
                'verbose_name': 'Realtor',
                'verbose_name_plural': 'Realtors',
            },
        ),
        migrations.CreateModel(
            name='ProxyUser',
            fields=[
            ],
            options={
                'verbose_name': 'User',
                'proxy': True,
                'verbose_name_plural': 'Users',
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='realtor',
            name='user',
            field=models.OneToOneField(verbose_name=b'User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='homebuyer',
            name='user',
            field=models.OneToOneField(verbose_name=b'User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grade',
            name='homebuyer',
            field=models.ForeignKey(verbose_name=b'Homebuyer', to='core.Homebuyer'),
        ),
        migrations.AddField(
            model_name='grade',
            name='house',
            field=models.ForeignKey(verbose_name=b'House', to='core.House'),
        ),
        migrations.AddField(
            model_name='couple',
            name='realtor',
            field=models.ForeignKey(verbose_name=b'Realtor', to='core.Realtor'),
        ),
        migrations.AddField(
            model_name='categoryweight',
            name='homebuyer',
            field=models.ForeignKey(verbose_name=b'Homebuyer', to='core.Homebuyer'),
        ),
        migrations.AddField(
            model_name='category',
            name='couple',
            field=models.ForeignKey(verbose_name=b'Couple', to='core.Couple'),
        ),
        migrations.AlterUniqueTogether(
            name='house',
            unique_together=set([('nickname', 'couple')]),
        ),
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together=set([('house', 'category', 'homebuyer')]),
        ),
        migrations.AlterUniqueTogether(
            name='categoryweight',
            unique_together=set([('homebuyer', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('summary', 'couple')]),
        ),
    ]
