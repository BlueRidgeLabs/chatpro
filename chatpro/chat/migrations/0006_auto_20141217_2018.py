# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_auto_20141217_1856'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(related_name='messages', verbose_name='User', to='chat.User', help_text='The user who sent this message', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='contact',
            field=models.ForeignKey(related_name='messages', verbose_name='Contact', to='chat.Contact', help_text='The contact who sent this message', null=True),
            preserve_default=True,
        ),
    ]
