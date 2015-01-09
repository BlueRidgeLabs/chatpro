from __future__ import absolute_import, unicode_literals

from chatpro.utils import union
from dash.orgs.models import Org
from django.conf import settings
from enum import Enum
from temba import TembaClient
from temba.types import Contact as TembaContact


class ChangeType(Enum):
    created = 1
    updated = 2
    deleted = 3


def temba_sync_contact(org, contact, change_type):
    client = org.get_temba_client()

    if change_type == ChangeType.created:
        temba_contact = contact.as_temba()
        temba_contact = client.create_contact(temba_contact.name,
                                              temba_contact.urns,
                                              temba_contact.fields,
                                              temba_contact.groups)
        # update our contact with the new UUID from RapidPro
        contact.uuid = temba_contact.uuid
        contact.save()

    elif change_type == ChangeType.updated:
        # fetch contact so that we can merge with its URNs, fields and groups
        remote_contact = client.get_contact(contact.uuid)
        local_contact = contact.as_temba()
        merged_contact = temba_merge_contacts(org, local_contact, remote_contact)

        client.update_contact(merged_contact.uuid,
                              merged_contact.name,
                              merged_contact.urns,
                              merged_contact.fields,
                              merged_contact.groups)

    elif change_type == ChangeType.deleted:
        client.delete_contact(contact.uuid)


def temba_merge_contacts(org, first, second):
    """
    Merges two Temba contacts with priority given to the first
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't merge contacts with different UUIDs")

    # URNs are merged by scheme
    first_urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in first.urns]}
    urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in second.urns]}
    urns_by_scheme.update(first_urns_by_scheme)
    urns = ['%s:%s' % (scheme, path) for scheme, path in urns_by_scheme.iteritems()]

    fields = second.fields.copy()
    fields.update(first.fields)

    # ignore any of second's chat room groups
    chat_group_uuids = set([r.group_uuid for r in org.rooms.filter(is_active=True)])
    second_non_chat_groups = [g for g in second.groups if g not in chat_group_uuids]
    groups = union(first.groups, second_non_chat_groups)

    return TembaContact.create(uuid=first.uuid, name=first.name, urns=urns, fields=fields, groups=groups)


######################### Monkey patching for the Org class #########################


def _org_get_temba_client(org):
    return TembaClient(settings.SITE_API_HOST, org.api_token)

Org.get_temba_client = _org_get_temba_client
