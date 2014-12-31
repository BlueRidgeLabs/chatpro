# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users_ext', '0002_auto_20141229_1204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='full_name',
            field=models.CharField(help_text='The full name of this user', max_length=128, verbose_name='Full name'),
            preserve_default=True,
        ),
    ]
