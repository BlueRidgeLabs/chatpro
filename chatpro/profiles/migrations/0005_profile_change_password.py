# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20150115_0748'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='change_password',
            field=models.BooleanField(default=False, help_text='User must change password on next login'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='change_password',
            field=models.BooleanField(default=True, help_text='User must change password on next login'),
            preserve_default=True,
        ),
    ]
