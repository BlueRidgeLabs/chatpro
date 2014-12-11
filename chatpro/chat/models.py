from __future__ import unicode_literals

from dash.orgs.models import Org
from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.db import models
from django.utils.translation import ugettext_lazy as _
from temba import TembaClient
from .tasks import sync_room_groups_task


class User(AuthUser):
    """
    An extended user who can use and/or manage chat rooms
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='supervisors')

    chatname = models.CharField(max_length=12)

    @classmethod
    def create(cls, org, name, chatname, email, password, rooms=(), manage_rooms=()):
        user = cls.objects.create(is_active=True, org=org, chatname=chatname,
                                  username=email, email=email, first_name=name)
        user.set_password(password)
        user.set_org(org)
        user.org_editors.add(org)
        user.save()

        user.rooms.add(*rooms)
        user.manage_rooms.add(*manage_rooms)

        return user

    @classmethod
    def from_auth_user(cls, user):
        return cls.objects.prefetch_related('rooms').filter(user_ptr_id=user.pk).first()

    def get_all_rooms(self):
        """
        Gets all rooms which this user has access to
        """
        return (self.rooms.all() | self.manage_rooms.all()).distinct()

    @property
    def name(self):
        return self.first_name


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

    def __unicode__(self):
        return self.name


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact who is tied to a single room
    """
    uuid = models.CharField(max_length=36)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='contacts')

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this contact"))

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='contacts',
                             help_text=_("The name of the room which this contact belongs in"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    is_active = models.BooleanField(default=True, help_text="Whether this room is active")

    @classmethod
    def create(cls, org, name, urn, room, uuid):
        return cls.objects.create(org=org, name=name, urn=urn, room=room, uuid=uuid)

    def get_urn_as_tuple(self):
        return self.urn.split(':', 1)

    def __unicode__(self):
        return self.name if self.name else self.urn_path


######################### Monkey patching for the Auth User class #########################

def _auth_user_get_rooms(auth_user):
    if not hasattr(auth_user, '_rooms'):
        # org admins have implicit access to all rooms
        if auth_user.is_administrator():
            auth_user._rooms = None
        else:
            user = User.from_auth_user(auth_user)
            if user:
                auth_user._rooms = user.get_all_rooms()
            else:
                auth_user._rooms = []

    return auth_user._rooms


def _auth_user_is_administrator(user):
    org_group = user.get_org_group()
    return org_group and org_group.name == 'Administrators'


AuthUser.get_rooms = _auth_user_get_rooms
AuthUser.is_administrator = _auth_user_is_administrator


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
    group_names = {group['uuid']: group['name'] for group in groups}

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
