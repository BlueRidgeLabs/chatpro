# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0008_org_timezone'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_uuid', models.CharField(unique=True, max_length=36)),
                ('name', models.CharField(help_text='Name of this room', max_length=128, verbose_name='Name', blank=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this room is active')),
                ('managers', models.ManyToManyField(help_text='Users who can manage contacts in this room', related_name='manage_rooms', verbose_name='Managers', to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(related_name='rooms', verbose_name='Organization', to='orgs.Org')),
                ('users', models.ManyToManyField(help_text='Users who can chat in this room', related_name='rooms', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
