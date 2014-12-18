from __future__ import unicode_literals

from dash.orgs.models import Org
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from temba import TembaClient
from .tasks import sync_room_groups_task


class Room(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    group_uuid = models.CharField(max_length=36)

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

    def __unicode__(self):
        return self.name


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact who is tied to a single room
    """
    uuid = models.CharField(max_length=36)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='contacts')

    name = models.CharField(verbose_name=_("Name"), max_length=128, null=True,
                            help_text=_("The name of this contact"))

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='contacts',
                             help_text=_("The room which this contact belongs in"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    comment = models.CharField(max_length=1000, blank=True)

    is_active = models.BooleanField(default=True, help_text="Whether this room is active")

    @classmethod
    def create(cls, org, name, urn, room, uuid):
        return cls.objects.create(org=org, name=name, urn=urn, room=room, uuid=uuid)

    def get_urn(self):
        return self.urn.split(':', 1)

    def __unicode__(self):
        return self.name if self.name else self.urn_path


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
    def create_incoming(cls, org, urn, text, room, time):
        if ':' in text:
            chat_name, text = text.split(': ', 1)  # remove name: from text

        contact = Contact.objects.get(urn=urn)

        return cls.objects.create(org=org, contact=contact, text=text, room=room, time=time)

    @classmethod
    def create_for_user(cls, org, user, text, room):
        return cls.objects.create(org=org, user=user, text=text, room=room, time=timezone.now())

    def get_sender(self):
        return self.contact if self.contact_id else self.user

    def as_json(self):
        sender = self.get_sender()
        sender_name = sender.name if isinstance(sender, Contact) else sender.full_name

        return dict(contact_id=self.contact_id, user_id=self.user_id, sender_name=sender_name,
                    text=self.text, room_id=self.room_id, time=self.time)


######################### Monkey patching for the User class #########################

def _user_create(cls, org, full_name, chat_name, email, password, rooms=(), manage_rooms=()):
    user = cls.objects.create(first_name=full_name, last_name=chat_name,
                              is_active=True, username=email, email=email)
    user.set_password(password)
    user.set_org(org)
    user.org_editors.add(org)
    user.save()

    user.rooms.add(*rooms)
    user.manage_rooms.add(*manage_rooms)

    return user


def _user_get_all_rooms(user):
    if not hasattr(user, '_rooms'):
        # org admins have implicit access to all rooms
        if user.is_administrator():
            user._rooms = Room.get_all(user.get_org())
        else:
            user._rooms = (user.rooms.filter(is_active=True) | user.manage_rooms.filter(is_active=True)).distinct()

    return user._rooms


def _user_is_administrator(user):
    org_group = user.get_org_group()
    return org_group and org_group.name == 'Administrators'


User.create = classmethod(_user_create)
User.full_name = property(lambda self: self.first_name)
User.chat_name = property(lambda self: self.last_name)
User.get_all_rooms = _user_get_all_rooms
User.is_administrator = _user_is_administrator


######################### Monkey patching for the Org class #########################


def _org_get_temba_client(org):
    return TembaClient(settings.SITE_API_HOST, org.api_token)


def _org_update_room_groups(org, group_uuids):
    """
    Updates an orgs chat rooms based on the selected groups UUIDs
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
            Room.create(org, group_names[group_uuid], group_uuid)

    sync_room_groups_task.delay(org.id, group_uuids)


Org.get_temba_client = _org_get_temba_client
Org.update_room_groups = _org_update_room_groups
