# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='chat_name',
            field=models.CharField(help_text='Shorter name used for chat messages', max_length=16, null=True, verbose_name='Chat name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='profile',
            name='full_name',
            field=models.CharField(max_length=128, null=True, verbose_name='Full name'),
            preserve_default=True,
        ),
    ]
