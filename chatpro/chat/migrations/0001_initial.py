# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0009_auto_20141210_1555'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36)),
                ('name', models.CharField(help_text='The name of this contact', max_length=128, verbose_name='Name', blank=True)),
                ('urn', models.CharField(max_length=255, verbose_name='URN')),
                ('comment', models.CharField(max_length=1000, blank=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this room is active')),
                ('org', models.ForeignKey(related_name='contacts', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=640)),
                ('time', models.DateTimeField(help_text='The time when this message was sent', verbose_name='Time')),
                ('contact', models.ForeignKey(related_name='messages', verbose_name='Contact', to='chat.Contact', help_text='The contact who sent this message', null=True)),
                ('org', models.ForeignKey(related_name='messages', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_uuid', models.CharField(max_length=36)),
                ('name', models.CharField(help_text='The name of this room', max_length=128, verbose_name='Name', blank=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this room is active')),
                ('managers', models.ManyToManyField(help_text='Users who can manage contacts in this room', related_name='manage_rooms', verbose_name='Managers', to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(related_name='rooms', verbose_name='Organization', to='orgs.Org')),
                ('users', models.ManyToManyField(help_text='Users who can chat in this room', related_name='rooms', verbose_name='Users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='message',
            name='room',
            field=models.ForeignKey(related_name='messages', verbose_name='Room', to='chat.Room', help_text='The room which this message was sent to'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(related_name='messages', verbose_name='User', to=settings.AUTH_USER_MODEL, help_text='The user who sent this message', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='room',
            field=models.ForeignKey(related_name='contacts', verbose_name='Room', to='chat.Room', help_text='The room which this contact belongs in'),
            preserve_default=True,
        ),
    ]
