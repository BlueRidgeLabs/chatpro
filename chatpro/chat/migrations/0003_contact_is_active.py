# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_room_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this room is active'),
            preserve_default=True,
        ),
    ]
