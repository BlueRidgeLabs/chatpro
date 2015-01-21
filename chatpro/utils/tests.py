from __future__ import absolute_import, unicode_literals

from chatpro.profiles.models import Contact
from chatpro.rooms.models import Room
from chatpro.test import ChatProTest
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact
from .temba import temba_pull_contacts


class TembaTest(ChatProTest):
    @patch('dash.orgs.models.TembaClient.get_contacts')
    def test_temba_pull_contacts(self, mock_get_contacts):
        # RapidPro returning no changes
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
                                fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-002', name="Bob", urns=['tel:2345'], groups=['000-001'],
                                fields=dict(chat_name="bob"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-003', name="Cat", urns=['tel:3456'], groups=['000-002'],
                                fields=dict(chat_name="cat"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-004', name="Dan", urns=['twitter:danny'], groups=['000-002'],
                                fields=dict(chat_name="dan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-005', name="Eve", urns=['twitter:evee'], groups=['000-003'],
                                fields=dict(chat_name="eve"), language='eng', modified_on=timezone.now())
        ]

        room_uuids = [r.uuid for r in self.unicef.rooms.all()]

        created, updated, deleted = temba_pull_contacts(self.unicef, room_uuids, Room, Contact)
        self.assertFalse(created or updated or deleted)

        # RapidPro returning 1 new, 1 modified and 1 deleted contact
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='000-001', name="Annie", urns=['tel:5678'], groups=['000-002'],
                                fields=dict(chat_name="annie"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-003', name="Cat", urns=['tel:3456'], groups=['000-002'],
                                fields=dict(chat_name="cat"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-004', name="Dan", urns=['twitter:danny'], groups=['000-002'],
                                fields=dict(chat_name="dan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-005', name="Eve", urns=['twitter:evee'], groups=['000-003'],
                                fields=dict(chat_name="eve"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-007', name="Jim", urns=['twitter:jimbo'], groups=['000-003'],
                                fields=dict(chat_name="jim"), language='eng', modified_on=timezone.now())
        ]

        created, updated, deleted = temba_pull_contacts(self.unicef, room_uuids, Room, Contact)
        self.assertEqual(sorted(created), ['000-007'])
        self.assertEqual(sorted(updated), ['000-001'])
        self.assertEqual(sorted(deleted), ['000-002'])

        # check created contact
        jim = Contact.objects.get(uuid='000-007')
        self.assertEqual(jim.full_name, "Jim")
        self.assertEqual(jim.chat_name, "jim")
        self.assertEqual(jim.urn, 'twitter:jimbo')
        self.assertEqual(jim.room, self.room3)

        # check modified contact
        ann = Contact.objects.get(uuid='000-001')
        self.assertEqual(ann.full_name, "Annie")
        self.assertEqual(ann.chat_name, "annie")
        self.assertEqual(ann.urn, 'tel:5678')
        self.assertEqual(ann.room, self.room2)

        # check deleted contact
        bob = Contact.objects.get(uuid='000-002')
        self.assertFalse(bob.is_active)
