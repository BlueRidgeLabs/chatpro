from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User


######################### Monkey patching for the User class #########################

def _user_is_admin_for(user, org):
    """
    Whether this user is an administrator for the given org
    """
    return org.administrators.filter(pk=user.pk).exists()


User.is_admin_for = _user_is_admin_for


######################### Monkey patching for the Org class #########################

ORG_CONFIG_SECRET_TOKEN = 'secret_token'
ORG_CONFIG_CHAT_NAME_FIELD = 'chat_name_field'


def _org_get_secret_token(org):
    return org.get_config(ORG_CONFIG_SECRET_TOKEN)


def _org_get_chat_name_field(org):
    return org.get_config(ORG_CONFIG_CHAT_NAME_FIELD)


Org.get_secret_token = _org_get_secret_token
Org.get_chat_name_field = _org_get_chat_name_field
