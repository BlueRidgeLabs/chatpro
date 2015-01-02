# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0009_auto_20141210_1555'),
        ('rooms', '0001_initial'),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=640)),
                ('time', models.DateTimeField(help_text='The time when this message was sent', verbose_name='Time')),
                ('org', models.ForeignKey(related_name='messages', verbose_name='Organization', to='orgs.Org')),
                ('profile', models.ForeignKey(related_name='messages', verbose_name='Profile', to='profiles.Profile', help_text='The profile that sent this message', null=True)),
                ('room', models.ForeignKey(related_name='messages', verbose_name='Room', to='rooms.Room', help_text='The room which this message was sent to')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
