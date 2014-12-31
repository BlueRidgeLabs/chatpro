# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_auto_20141230_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='chat_name',
            field=models.CharField(help_text='The chat name of this contact', max_length=16, null=True, verbose_name='Chat name'),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='contact',
            old_name='name',
            new_name='full_name',
        ),
        migrations.AlterField(
            model_name='contact',
            name='full_name',
            field=models.CharField(help_text='The full name of this contact', max_length=128, null=True, verbose_name='Full name'),
            preserve_default=True,
        ),
    ]
