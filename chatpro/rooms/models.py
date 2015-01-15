from __future__ import absolute_import, unicode_literals

from chatpro.profiles.tasks import sync_org_contacts
from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Room(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='rooms')

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("Name of this room"))

    users = models.ManyToManyField(User, verbose_name=_("Users"), related_name='rooms',
                                   help_text=_("Users who can chat in this room"))

    managers = models.ManyToManyField(User, verbose_name=_("Managers"), related_name='manage_rooms',
                                      help_text=_("Users who can manage contacts in this room"))

    is_active = models.BooleanField(default=True, help_text="Whether this room is active")

    @classmethod
    def create(cls, org, name, uuid):
        return Room.objects.create(org=org, name=name, uuid=uuid)

    @classmethod
    def get_all(cls, org):
        return Room.objects.filter(org=org, is_active=True)

    @classmethod
    def update_room_groups(cls, org, group_uuids):
        """
        Updates an org's chat rooms based on the selected groups UUIDs
        """
        # de-activate rooms not included
        org.rooms.exclude(uuid__in=group_uuids).update(is_active=False)

        # fetch group details
        groups = org.get_temba_client().get_groups()
        group_names = {group.uuid: group.name for group in groups}

        for group_uuid in group_uuids:
            existing = org.rooms.filter(uuid=group_uuid).first()
            if existing:
                existing.name = group_names[group_uuid]
                existing.is_active = True
                existing.save()
            else:
                cls.create(org, group_names[group_uuid], group_uuid)

        sync_org_contacts.delay(org.id)

    def get_contacts(self):
        return self.contacts.filter(is_active=True)

    def get_users(self):
        return self.users.filter(is_active=True).select_related('profile')

    def get_managers(self):
        return self.managers.filter(is_active=True).select_related('profile')

    def __unicode__(self):
        return self.name
