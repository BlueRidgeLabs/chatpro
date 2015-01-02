from __future__ import unicode_literals

from celery import shared_task
from collections import defaultdict
from dash.orgs.models import Org


@shared_task
def sync_room_groups_task(org_id, group_uuids):
    from chatpro.rooms.models import Room
    from chatpro.profiles.models import Profile

    print 'Starting room group sync task: org_id=%d, group_uuids=[%s]' % (org_id, ",".join(group_uuids))

    org = Org.objects.get(pk=org_id)
    client = org.get_temba_client()
    chat_name_field = org.get_chat_name_field()

    incoming_contacts = client.get_contacts(group_uuids=group_uuids)

    # organize incoming contacts by the UUID of their first group
    incoming_by_group = defaultdict(list)
    for contact in incoming_contacts:
        if contact.group_uuids and contact.urns:
            group_uuid = contact.group_uuids[0]
            incoming_by_group[group_uuid].append(contact)

    existing_contacts = org.contacts.all()
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    created_uuids = []
    updated_uuids = set()
    deleted_uuids = []

    for room in Room.objects.filter(group_uuid__in=group_uuids):
        incoming_contacts = incoming_by_group[room.group_uuid]

        for temba_contact in incoming_contacts:
            if temba_contact.uuid in existing_by_uuid:
                existing = existing_by_uuid[temba_contact.uuid]

                existing.is_active = True
                existing.urn = temba_contact.urns[0]
                existing.save()

                existing.profile.full_name = temba_contact.name
                existing.profile.chat_name = temba_contact.fields.get(chat_name_field, None)
                existing.profile.save()

                updated_uuids.add(temba_contact.uuid)
            else:
                Profile.from_temba(org, room, temba_contact)
                created_uuids.append(temba_contact.uuid)

    for existing_uuid in existing_by_uuid.keys():
        if existing_uuid not in updated_uuids:
            deleted_uuids.append(existing_uuid)

    org.contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    print "Finished contact sync (%d created, %d updated, %d deleted)" % (len(created_uuids), len(updated_uuids), len(deleted_uuids))
