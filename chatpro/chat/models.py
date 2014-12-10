from __future__ import unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Room(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    group_uuid = models.CharField(max_length=36)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='rooms')

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this room"))

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

    @classmethod
    def create(cls, org, name, urn, room, uuid):
        return cls.objects.create(org=org, name=name, urn=urn, room=room, uuid=uuid)

    def __unicode__(self):
        return self.name if self.name else self.urn_path


class Supervisor(User):
    """
    An editor user who can supervise chat rooms
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='supervisors')

    rooms = models.ManyToManyField(Room, verbose_name=_("Rooms"), related_name='supervisors')

    @classmethod
    def create(cls, org, name, email, password, rooms):
        supervisor = cls.objects.create(is_active=True, org=org, username=email, email=email, first_name=name)
        supervisor.set_password(password)
        supervisor.set_org(org)
        supervisor.org_editors.add(org)
        supervisor.rooms.add(*rooms)
        supervisor.save()
        return supervisor

    @classmethod
    def from_user(cls, user):
        return cls.objects.prefetch_related('rooms').filter(user_ptr_id=user.pk).first()

    @property
    def name(self):
        return self.first_name


######################### Monkey patching for the User class #########################

def _user_get_rooms(user):
    if not hasattr(user, '_rooms'):
        # org admins have implicit access to all rooms
        if user.is_administrator():
            user._rooms = None
        else:
            supervisor = Supervisor.from_user(user)
            if supervisor:
                user._rooms = supervisor.rooms.all()
            else:
                user._rooms = []

    return user._rooms


def _user_is_administrator(user):
    org_group = user.get_org_group()
    return org_group and org_group.name == 'Administrators'


User.get_rooms = _user_get_rooms
User.is_administrator = _user_is_administrator
