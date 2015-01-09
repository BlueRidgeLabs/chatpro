from __future__ import absolute_import, unicode_literals

from chatpro.rooms.models import Room
from django.contrib.auth.models import User
from .models import Profile


######################### Monkey patching for the User class #########################

def _user_create(cls, org, full_name, chat_name, email, password, rooms=(), manage_rooms=()):
    """
    Creates a regular user with specific room-level permissions
    """
    # create auth user
    user = cls.objects.create(is_active=True, username=email, email=email)
    user.set_password(password)
    user.save()

    # add profile
    Profile.objects.create(user=user, full_name=full_name, chat_name=chat_name)

    # setup as org editor with limited room permissions
    if org:
        user.org_editors.add(org)
    if rooms or manage_rooms:
        user.update_rooms(rooms, manage_rooms)
    return user


def _user_has_profile(user):
    from chatpro.profiles.models import Profile
    try:
        return bool(user.profile)
    except Profile.DoesNotExist:
        return False


def _user_get_full_name(user):
    """
    Override regular get_full_name which returns first_name + last_name
    """
    return user.profile.full_name if user.has_profile() else " ".join([user.first_name, user.last_name]).strip()


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


User.create = classmethod(_user_create)
User.has_profile = _user_has_profile
User.get_full_name = _user_get_full_name
User.get_rooms = _user_get_rooms
User.update_rooms = _user_update_rooms
User.has_room_access = _user_has_room_access
