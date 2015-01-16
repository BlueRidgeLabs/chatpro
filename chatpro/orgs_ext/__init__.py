from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org

######################### Monkey patching for the Org class #########################

ORG_CONFIG_SECRET_TOKEN = 'secret_token'
ORG_CONFIG_CHAT_NAME_FIELD = 'chat_name_field'


def _org_get_secret_token(org):
    return org.get_config(ORG_CONFIG_SECRET_TOKEN)


def _org_get_chat_name_field(org):
    return org.get_config(ORG_CONFIG_CHAT_NAME_FIELD)


Org.get_secret_token = _org_get_secret_token
Org.get_chat_name_field = _org_get_chat_name_field
