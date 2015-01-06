from __future__ import unicode_literals

from celery import shared_task
from enum import Enum


class ChangeType(Enum):
    created = 1
    updated = 2
    deleted = 3


@shared_task
def push_contact_change_task(contact_id, change_type):
    """
    Task to push a local contact change to RapidPro
    """
    from chatpro.profiles.models import Contact

    contact = Contact.objects.get(pk=contact_id)
    temba_contact = contact.to_temba()
    org = contact.org
    client = org.get_temba_client()

    print "Pushing %s change to contact %s" % (change_type.name.upper(), contact.uuid)

    if change_type == ChangeType.created:
        temba_contact = client.create_contact(temba_contact.name,
                                              temba_contact.urns,
                                              temba_contact.fields,
                                              temba_contact.group_uuids)
        # update our contact with the new UUID from RapidPro
        contact.uuid = temba_contact.uuid
        contact.save()

    elif change_type == ChangeType.updated:
        temba_contact = contact.to_temba()
        client.update_contact(temba_contact.uuid,
                              temba_contact.name,
                              temba_contact.urns,
                              temba_contact.fields,
                              temba_contact.group_uuids)

    elif change_type == ChangeType.deleted:
        client.delete_contact(temba_contact.uuid)
