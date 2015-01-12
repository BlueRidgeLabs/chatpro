# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='room',
            old_name='group_uuid',
            new_name='uuid',
        ),
    ]
