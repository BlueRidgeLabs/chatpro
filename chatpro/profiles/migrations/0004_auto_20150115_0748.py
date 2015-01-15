# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def migrate_contact_profiles(apps, schema_editor):
    Profile = apps.get_model("profiles", "Profile")

    for profile in Profile.objects.filter(user=None).select_related('contact'):
        profile.contact.full_name = profile.full_name
        profile.contact.chat_name = profile.chat_name
        profile.contact.save()

        profile.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_auto_20150108_1230'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='chat_name',
            field=models.CharField(help_text='Shorter name used for chat messages', max_length=16, null=True, verbose_name='Chat name'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='full_name',
            field=models.CharField(max_length=128, null=True, verbose_name='Full name'),
            preserve_default=True,
        ),
        migrations.RunPython(migrate_contact_profiles),
        migrations.RemoveField(
            model_name='profile',
            name='contact',
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
