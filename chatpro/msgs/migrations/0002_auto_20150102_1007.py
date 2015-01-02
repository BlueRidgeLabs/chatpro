# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='profile',
            new_name='sender',
        ),
    ]
