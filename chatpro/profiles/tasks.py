from __future__ import absolute_import, unicode_literals

import logging

from chatpro.utils.temba import temba_sync_contact, temba_pull_contacts
from dash.orgs.models import Org
from djcelery_transactions import task

logger = logging.getLogger(__name__)


@task
def push_contact_change(contact_id, change_type):
    """
    Task to push a local contact change to RapidPro
    """
    from .models import Contact

    contact = Contact.objects.select_related('org', 'room').get(pk=contact_id)
    org = contact.org

    logger.info("Pushing %s change to contact %s" % (change_type.name.upper(), contact.uuid))

    chat_group_uuids = set([r.uuid for r in org.rooms.filter(is_active=True)])

    temba_sync_contact(org, contact, change_type, chat_group_uuids)


@task
def sync_org_contacts(org_id):
    """
    Syncs all contacts for the given org
    """
    from chatpro.profiles.models import Contact
    from chatpro.rooms.models import Room

    org = Org.objects.get(pk=org_id)
    rooms = org.rooms.all()
    primary_groups = [r.uuid for r in rooms]

    logger.info('Starting contact sync task for org #%d' % org.id)

    created, updated, deleted = temba_pull_contacts(org, primary_groups, Room, Contact)

    logger.info("Finished contact sync for org #%d (%d created, %d updated, %d deleted)"
                % (org.id, len(created), len(updated), len(deleted)))


@task
def sync_all_contacts():
    """
    Syncs all contacts for all orgs
    """
    for org in Org.objects.filter(is_active=True):
        sync_org_contacts(org.id)
