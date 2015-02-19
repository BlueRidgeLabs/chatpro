from __future__ import absolute_import, unicode_literals

import json

from dash.orgs.models import Org
from dash.utils import random_string
from django.core.cache import cache
from enum import Enum


class TaskType(Enum):
    sync_contacts = 1
    fetch_runs = 2


LAST_TASK_CACHE_KEY = 'org:%d:task_result:%s'
LAST_TASK_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week


######################### Monkey patching for the Org class #########################

ORG_CONFIG_SECRET_TOKEN = 'secret_token'
ORG_CONFIG_CHAT_NAME_FIELD = 'chat_name_field'


def _org_get_secret_token(org):
    return org.get_config(ORG_CONFIG_SECRET_TOKEN)


def _org_get_chat_name_field(org):
    return org.get_config(ORG_CONFIG_CHAT_NAME_FIELD)


def _org_clean(org):
    super(Org, org).clean()

    # set config defaults
    if not org.config:
        org.config = json.dumps({ORG_CONFIG_SECRET_TOKEN: random_string(16).lower(),
                                 ORG_CONFIG_CHAT_NAME_FIELD: 'chat_name'})


def _org_get_task_result(org, task_type):
    result = cache.get(LAST_TASK_CACHE_KEY % (org.pk, task_type.name))
    return json.loads(result) if result is not None else None


def _org_set_task_result(org, task_type, result):
    cache.set(LAST_TASK_CACHE_KEY % (org.pk, task_type.name), json.dumps(result), LAST_TASK_CACHE_TTL)


Org.get_secret_token = _org_get_secret_token
Org.get_chat_name_field = _org_get_chat_name_field
Org.clean = _org_clean
Org.get_task_result = _org_get_task_result
Org.set_task_result = _org_set_task_result
