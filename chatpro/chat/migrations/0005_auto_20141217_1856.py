# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0009_auto_20141210_1555'),
        ('chat', '0004_contact_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=640)),
                ('time', models.DateTimeField(help_text='The time when this message was sent', verbose_name='Time')),
                ('contact', models.ForeignKey(related_name='messages', verbose_name='Contact', to='chat.Contact', help_text='The contact who sent this message')),
                ('org', models.ForeignKey(related_name='messages', verbose_name='Organization', to='orgs.Org')),
                ('room', models.ForeignKey(related_name='messages', verbose_name='Room', to='chat.Room', help_text='The room which this message was sent to')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='contact',
            name='room',
            field=models.ForeignKey(related_name='contacts', verbose_name='Room', to='chat.Room', help_text='The room which this contact belongs in'),
            preserve_default=True,
        ),
    ]
