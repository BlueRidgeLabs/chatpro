# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_contact_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='comment',
            field=models.CharField(max_length=1000, blank=True),
            preserve_default=True,
        ),
    ]
