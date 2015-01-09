from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from chatpro.utils import intersection
from chatpro.utils.temba import temba_sync_contact
from collections import defaultdict
from dash.orgs.models import Org

logger = logging.getLogger(__name__)


@shared_task
def push_contact_change(contact_id, change_type):
    """
    Task to push a local contact change to RapidPro
    """
    from .models import Contact

    contact = Contact.objects.select_related('org', 'room').get(pk=contact_id)
    org = contact.org

    logger.info("Pushing %s change to contact %s" % (change_type.name.upper(), contact.uuid))

    temba_sync_contact(org, contact, change_type)


@shared_task
def sync_org_contacts(org_id):
    """
    Syncs all contacts for the given org
    """
    from chatpro.profiles.models import Contact

    logger.info('Starting contact sync task for org #%d' % org_id)

    org = Org.objects.get(pk=org_id)
    client = org.get_temba_client()
    chat_name_field = org.get_chat_name_field()
    rooms = org.rooms.all()

    group_uuids = [r.group_uuid for r in rooms]

    incoming_contacts = client.get_contacts(groups=group_uuids)

    # organize incoming contacts by the UUID of their first group
    incoming_by_group = defaultdict(list)
    for incoming_contact in incoming_contacts:
        # ignore contacts with no URN
        if not incoming_contact.urns:
            logger.warning("Ignoring contact %s with no URN" % incoming_contact.uuid)
            continue

        # which chat rooms is this contact in?
        chat_group_uuids = intersection(incoming_contact.groups, group_uuids)

        if len(chat_group_uuids) != 1:
            logger.warning("Ignoring contact %s who is in multiple chat room groups" % incoming_contact.uuid)
            continue

        group_uuid = chat_group_uuids[0]
        incoming_by_group[group_uuid].append(incoming_contact)

    existing_contacts = org.contacts.all()
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    created_uuids = []
    updated_uuids = set()
    deleted_uuids = []

    for room in rooms:
        incoming_contacts = incoming_by_group[room.group_uuid]

        for incoming in incoming_contacts:
            if incoming.uuid in existing_by_uuid:
                existing = existing_by_uuid[incoming.uuid]

                existing.room = room
                existing.is_active = True
                existing.urn = incoming.urns[0]
                existing.save()

                existing.profile.full_name = incoming.name
                existing.profile.chat_name = incoming.fields.get(chat_name_field, None)
                existing.profile.save()

                updated_uuids.add(incoming.uuid)
            else:
                created = Contact.from_temba(org, room, incoming)
                created_uuids.append(created.uuid)

    # any existing contact not updated, is now deleted
    for existing_uuid in existing_by_uuid.keys():
        if existing_uuid not in updated_uuids:
            deleted_uuids.append(existing_uuid)

    org.contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    logger.info("Finished contact sync for org #%d (%d created, %d updated, %d deleted)"
                % (org_id, len(created_uuids), len(updated_uuids), len(deleted_uuids)))


@shared_task
def sync_all_contacts():
    """
    Syncs all contacts for all orgs
    """
    for org in Org.objects.filter(is_active=True):
        sync_org_contacts(org.id)
