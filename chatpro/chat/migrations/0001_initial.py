# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('orgs', '0009_auto_20141210_1555'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36)),
                ('name', models.CharField(help_text='The name of this contact', max_length=128, verbose_name='Name', blank=True)),
                ('urn', models.CharField(max_length=255, verbose_name='URN')),
                ('org', models.ForeignKey(related_name='contacts', verbose_name='Organization', to='orgs.Org')),
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
                ('org', models.ForeignKey(related_name='rooms', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Supervisor',
            fields=[
                ('user_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(related_name='supervisors', verbose_name='Organization', to='orgs.Org')),
                ('rooms', models.ManyToManyField(related_name='supervisors', verbose_name='Rooms', to='chat.Room')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=('auth.user',),
        ),
        migrations.AddField(
            model_name='contact',
            name='room',
            field=models.ForeignKey(related_name='contacts', verbose_name='Room', to='chat.Room', help_text='The name of the room which this contact belongs in'),
            preserve_default=True,
        ),
    ]
