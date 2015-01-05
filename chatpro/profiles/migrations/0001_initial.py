# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0008_org_timezone'),
        ('rooms', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=36)),
                ('urn', models.CharField(max_length=255, verbose_name='URN')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this contact is active')),
                ('org', models.ForeignKey(related_name='contacts', verbose_name='Organization', to='orgs.Org')),
                ('room', models.ForeignKey(related_name='contacts', verbose_name='Room', to='rooms.Room', help_text='Room which this contact belongs in')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=128, verbose_name='Full name')),
                ('chat_name', models.CharField(help_text='Shorter name used for chat messages', max_length=16, verbose_name='Chat name')),
                ('contact', models.OneToOneField(null=True, to='profiles.Contact')),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
