from __future__ import unicode_literals

from chatpro.chat.models import Room
from dash.orgs.models import Org
from django.conf import settings
from django.contrib.auth.models import User
from temba import TembaClient
from .tasks import sync_room_groups_task


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


def _user_get_full_name(user):
    return user.first_name


def _user_is_administrator(user):
    org_group = user.get_org_group()
    return org_group and org_group.name == 'Administrators'


User.create = classmethod(_user_create)
User.full_name = property(lambda self: self.first_name)
User.chat_name = property(lambda self: self.last_name)
User.get_full_name = _user_get_full_name
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