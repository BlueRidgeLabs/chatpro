from __future__ import absolute_import, unicode_literals

import logging

from chatpro.utils import intersection, union
from collections import defaultdict
from dash.orgs.models import Org
from django.conf import settings
from enum import Enum
from temba import TembaClient
from temba.types import Contact as TembaContact

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    created = 1
    updated = 2
    deleted = 3


def temba_sync_contact(org, contact, change_type, primary_groups):
    """
    Syncs a local change to a contact
    :param org: the org
    :param contact: the contact
    :param change_type: the change type
    :param primary_groups: a set of group UUIDs which represent the primary groups for this org. Membership of primary
    groups is mutually exclusive
    """
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

        if temba_compare_contacts(remote_contact, local_contact):
            merged_contact = temba_merge_contacts(local_contact, remote_contact, primary_groups)

            client.update_contact(merged_contact.uuid,
                                  merged_contact.name,
                                  merged_contact.urns,
                                  merged_contact.fields,
                                  merged_contact.groups)

    elif change_type == ChangeType.deleted:
        client.delete_contact(contact.uuid)


def temba_pull_contacts(org, primary_groups, group_class, contact_class):
    """
    Pulls contacts from RapidPro and syncs with local contacts
    """
    client = org.get_temba_client()

    # get all existing contacts and organize by their UUID
    existing_contacts = contact_class.objects.filter(org=org)
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    # get all remote contacts in our primary groups
    incoming_contacts = client.get_contacts(groups=primary_groups)

    # organize incoming contacts by the UUID of their primary group
    incoming_by_primary = defaultdict(list)
    incoming_uuids = set()
    for incoming_contact in incoming_contacts:
        # ignore contacts with no URN
        if not incoming_contact.urns:
            logger.warning("Ignoring contact %s with no URN" % incoming_contact.uuid)
            continue

        # which primary groups is this contact in?
        contact_primary_groups = intersection(incoming_contact.groups, primary_groups)

        if len(contact_primary_groups) != 1:
            logger.warning("Ignoring contact %s who is in multiple primary groups" % incoming_contact.uuid)
            continue

        incoming_by_primary[contact_primary_groups[0]].append(incoming_contact)
        incoming_uuids.add(incoming_contact.uuid)

    created_uuids = []
    updated_uuids = []
    deleted_uuids = []

    for primary_group in primary_groups:
        incoming_contacts = incoming_by_primary[primary_group]
        group_obj = group_class.objects.get(uuid=primary_group)

        for incoming in incoming_contacts:
            if incoming.uuid in existing_by_uuid:
                existing = existing_by_uuid[incoming.uuid]

                if temba_compare_contacts(incoming, existing.as_temba()) or not existing.is_active:
                    existing.update_from_temba(org, group_obj, incoming)
                    updated_uuids.append(incoming.uuid)
            else:
                created = contact_class.from_temba(org, group_obj, incoming)
                created_uuids.append(created.uuid)

    # any existing contact not in the incoming set, is now deleted if not already deleted
    for existing_uuid, existing in existing_by_uuid.iteritems():
        if existing_uuid not in incoming_uuids and existing.is_active:
            deleted_uuids.append(existing_uuid)

    existing_contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    return created_uuids, updated_uuids, deleted_uuids


def temba_compare_contacts(first, second):
    """
    Compares two Temba contacts to determine if there are differences
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't compare contacts with different UUIDs")

    return first.name != second.name or sorted(first.urns) != sorted(second.urns) or first.fields != second.fields or sorted(first.groups) != sorted(second.groups)


def temba_merge_contacts(first, second, primary_groups):
    """
    Merges two Temba contacts, with priority given to the first contact
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't merge contacts with different UUIDs")

    # URNs are merged by scheme
    first_urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in first.urns]}
    urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in second.urns]}
    urns_by_scheme.update(first_urns_by_scheme)
    merged_urns = ['%s:%s' % (scheme, path) for scheme, path in urns_by_scheme.iteritems()]

    # fields are simple key based merge
    merged_fields = second.fields.copy()
    merged_fields.update(first.fields)

    # helper method to split contact groups into single primary and remaining secondary groups
    def split_groups(groups):
        primary, secondary = None, []
        for g in groups:
            if g in primary_groups:
                primary = g
            else:
                secondary.append(g)
        return primary, secondary

    # group merging honors given list of mutually exclusive primary groups
    first_primary_group, first_secondary_groups = split_groups(first.groups)
    second_primary_group, second_secondary_groups = split_groups(second.groups)
    primary_group = first_primary_group or second_primary_group
    merged_groups = union(first_secondary_groups, second_secondary_groups, [primary_group] if primary_group else [])

    return TembaContact.create(uuid=first.uuid, name=first.name,
                               urns=merged_urns, fields=merged_fields, groups=merged_groups)


######################### Monkey patching for the Org class #########################


def _org_get_temba_client(org):
    return TembaClient(settings.SITE_API_HOST, org.api_token)

Org.get_temba_client = _org_get_temba_client
