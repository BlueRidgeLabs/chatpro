# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import pytz

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0002_auto_20150102_0946'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='created_by',
            field=models.ForeignKey(related_name='contact_creations', to=settings.AUTH_USER_MODEL, help_text='The user which originally created this item', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0, 0, 0, pytz.utc), help_text='When this item was originally created', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contact',
            name='modified_by',
            field=models.ForeignKey(related_name='contact_modifications', to=settings.AUTH_USER_MODEL, help_text='The user which last modified this item', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='modified_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0, 0, 0, pytz.utc), help_text='When this item was last modified', auto_now=True),
            preserve_default=False,
        ),
    ]
