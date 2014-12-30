# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, migrations


def create_user_profiles(apps, schema_editor):
    Profile = apps.get_model("users_ext", "Profile")

    for user in User.objects.filter(profile=None):
        Profile.objects.create(user_id=user.id, full_name=user.first_name, chat_name=user.last_name)
        user.first_name = ""
        user.last_name = ""
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users_ext', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_user_profiles)
    ]
