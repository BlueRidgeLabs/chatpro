from __future__ import unicode_literals

from django.contrib.auth.models import User


######################### Monkey patching for the User class #########################

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


User.has_profile = _user_has_profile
User.get_full_name = _user_get_full_name