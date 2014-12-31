# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_auto_20141217_2230'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='uuid',
            field=models.CharField(unique=True, max_length=36),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='room',
            name='group_uuid',
            field=models.CharField(unique=True, max_length=36),
            preserve_default=True,
        ),
    ]
