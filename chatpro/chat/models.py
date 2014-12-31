from __future__ import unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from enum import Enum
from .tasks import sync_room_groups_task


class RoomPermission(Enum):
    read = 1
    send = 2
    manage = 3


class Room(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    group_uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='rooms')

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this room"))

    users = models.ManyToManyField(User, verbose_name=_("Users"), related_name='rooms',
                                   help_text=_("Users who can chat in this room"))

    managers = models.ManyToManyField(User, verbose_name=_("Managers"), related_name='manage_rooms',
                                      help_text=_("Users who can manage contacts in this room"))

    is_active = models.BooleanField(default=True, help_text="Whether this room is active")

    @classmethod
    def create(cls, org, name, group_uuid):
        return Room.objects.create(org=org, name=name, group_uuid=group_uuid)

    @classmethod
    def get_all(cls, org):
        return Room.objects.filter(org=org, is_active=True).order_by('name')

    @classmethod
    def update_room_groups(cls, org, group_uuids):
        """
        Updates an org's chat rooms based on the selected groups UUIDs
        """
        # de-activate rooms not included
        org.rooms.exclude(group_uuid__in=group_uuids).update(is_active=False)

        # fetch group details
        groups = org.get_temba_client().get_groups()
        group_names = {group.uuid: group.name for group in groups}

        for group_uuid in group_uuids:
            existing = org.rooms.filter(group_uuid=group_uuid).first()
            if existing:
                existing.name = group_names[group_uuid]
                existing.is_active = True
                existing.save()
            else:
                cls.create(org, group_names[group_uuid], group_uuid)

        sync_room_groups_task.delay(org.id, group_uuids)

    def __unicode__(self):
        return self.name


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact who is tied to a single room
    """
    uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='contacts')

    full_name = models.CharField(verbose_name=_("Full name"), max_length=128, null=True,
                                 help_text=_("The full name of this contact"))

    chat_name = models.CharField(verbose_name=_("Chat name"), max_length=16, null=True,
                                 help_text=_("The chat name of this contact"))

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='contacts',
                             help_text=_("The room which this contact belongs in"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    comment = models.CharField(max_length=1000, blank=True)

    is_active = models.BooleanField(default=True, help_text="Whether this room is active")

    @classmethod
    def create(cls, org, full_name, chat_name, urn, room, uuid):
        if org.id != room.org_id:
            raise ValueError("Room does not belong to org")

        return cls.objects.create(org=org, full_name=full_name, chat_name=chat_name, urn=urn, room=room, uuid=uuid)

    @classmethod
    def from_temba(cls, org, room, temba_contact):
        full_name = temba_contact.name
        chat_name = temba_contact.fields.get(org.get_chat_name_field(), None)
        urn = temba_contact.urns[0]
        return Contact.create(org, full_name, chat_name, urn, room, temba_contact.uuid)

    def get_urn(self):
        return tuple(self.urn.split(':', 1))

    def __unicode__(self):
        if self.full_name:
            return self.full_name
        elif self.chat_name:
            return self.chat_name
        else:
            return self.get_urn()[1]


class Message(models.Model):
    """
    Corresponds to a RapidPro message sent to a room
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='messages')

    contact = models.ForeignKey(Contact, null=True, verbose_name=_("Contact"), related_name='messages',
                                help_text=_("The contact who sent this message"))

    user = models.ForeignKey(User, null=True, verbose_name=_("User"), related_name='messages',
                             help_text=_("The user who sent this message"))

    text = models.CharField(max_length=640)

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='messages',
                             help_text=_("The room which this message was sent to"))

    time = models.DateTimeField(verbose_name=_("Time"), help_text=_("The time when this message was sent"))

    @classmethod
    def create_for_contact(cls, org, contact, text, room):
        if ':' in text:
            chat_name, text = text.split(': ', 1)  # remove name: from text

        return cls.objects.create(org=org, contact=contact, text=text, room=room, time=timezone.now())

    @classmethod
    def create_for_user(cls, org, user, text, room):
        return cls.objects.create(org=org, user=user, text=text, room=room, time=timezone.now())

    def get_sender(self):
        return self.contact if self.contact_id else self.user

    def as_json(self):
        sender = self.get_sender()
        sender_name = sender.full_name if isinstance(sender, Contact) else sender.profile.full_name

        return dict(message_id=self.pk,
                    contact_id=self.contact_id,
                    user_id=self.user_id,
                    sender_name=sender_name,
                    text=self.text,
                    room_id=self.room_id,
                    time=self.time)
