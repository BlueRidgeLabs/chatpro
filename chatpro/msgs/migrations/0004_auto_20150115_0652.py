# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def populate_user_and_contact(apps, schema_editor):
    Message = apps.get_model("msgs", "Message")
    for msg in Message.objects.all():
        if msg.sender.user_id:
            msg.user_id = msg.sender.user_id
        else:
            msg.contact_id = msg.sender.contact_id
        msg.save()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_auto_20150108_1230'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('msgs', '0003_message_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='contact',
            field=models.ForeignKey(related_name='messages', verbose_name='Contact', to='profiles.Contact', help_text='The contact that sent this message', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(related_name='messages', verbose_name='User', to=settings.AUTH_USER_MODEL, help_text='The user that sent this message', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(populate_user_and_contact),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
    ]
