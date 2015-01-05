from __future__ import unicode_literals

from django.contrib.auth.models import User
from .models import Room


######################### Monkey patching for the User class #########################

def _user_get_rooms(user, org):
    if not hasattr(user, '_rooms'):
        # org admins have implicit access to all rooms
        if user.is_admin_for(org):
            user._rooms = Room.get_all(org)
        else:
            user._rooms = user.rooms.filter(is_active=True)

    return user._rooms


def _user_update_rooms(user, rooms, manage_rooms):
    """
    Updates a user's rooms
    """
    user.rooms.clear()
    user.rooms.add(*rooms)
    user.rooms.add(*manage_rooms)

    user.manage_rooms.clear()
    user.manage_rooms.add(*manage_rooms)


def _user_has_room_access(user, room, manage=False):
    """
    Whether the given user has access to the given room
    """
    if user.is_superuser or user.is_admin_for(room.org):
        return True
    elif manage:
        return user.manage_rooms.filter(pk=room.pk).exists()
    else:
        return user.rooms.filter(pk=room.pk).exists()


User.get_rooms = _user_get_rooms
User.update_rooms = _user_update_rooms
User.has_room_access = _user_has_room_access
