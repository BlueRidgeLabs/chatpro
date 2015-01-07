# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0002_auto_20150102_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='status',
            field=models.CharField(default='S', help_text='Current status of this message', max_length=1, verbose_name='Status', choices=[('P', 'Pending'), ('S', 'Sent')]),
            preserve_default=False,
        ),
    ]
