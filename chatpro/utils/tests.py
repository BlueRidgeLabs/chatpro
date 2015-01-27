from __future__ import absolute_import, unicode_literals

from chatpro.profiles.models import Contact
from chatpro.test import ChatProTest
from dash.utils.sync import sync_pull_contacts
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact


class TembaTest(ChatProTest):
    @patch('dash.orgs.models.TembaClient.get_contacts')
    def test_sync_pull_contacts(self, mock_get_contacts):
        # RapidPro returning no changes
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='C-001', name="Ann", urns=['tel:1234'], groups=['G-001'],
                                fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-002', name="Bob", urns=['tel:2345'], groups=['G-001'],
                                fields=dict(chat_name="bob"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-003', name="Cat", urns=['tel:3456'], groups=['G-002'],
                                fields=dict(chat_name="cat"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-004', name="Dan", urns=['twitter:danny'], groups=['G-002'],
                                fields=dict(chat_name="dan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-005', name="Eve", urns=['twitter:evee'], groups=['G-003'],
                                fields=dict(chat_name="eve"), language='eng', modified_on=timezone.now())
        ]

        room_uuids = [r.uuid for r in self.unicef.rooms.all()]

        created, updated, deleted = sync_pull_contacts(self.unicef, room_uuids, Contact)
        self.assertFalse(created or updated or deleted)

        # RapidPro returning 1 new, 1 modified and 1 deleted contact
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='C-001', name="Annie", urns=['tel:5678'], groups=['G-002'],
                                fields=dict(chat_name="annie"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-003', name="Cat", urns=['tel:3456'], groups=['G-002'],
                                fields=dict(chat_name="cat"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-004', name="Dan", urns=['twitter:danny'], groups=['G-002'],
                                fields=dict(chat_name="dan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-005', name="Eve", urns=['twitter:evee'], groups=['G-003'],
                                fields=dict(chat_name="eve"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-007', name="Jim", urns=['twitter:jimbo'], groups=['G-003'],
                                fields=dict(chat_name="jim"), language='eng', modified_on=timezone.now())
        ]

        created, updated, deleted = sync_pull_contacts(self.unicef, room_uuids, Contact)
        self.assertEqual(sorted(created), ['C-007'])
        self.assertEqual(sorted(updated), ['C-001'])
        self.assertEqual(sorted(deleted), ['C-002'])

        # check created contact
        jim = Contact.objects.get(uuid='C-007')
        self.assertEqual(jim.full_name, "Jim")
        self.assertEqual(jim.chat_name, "jim")
        self.assertEqual(jim.urn, 'twitter:jimbo')
        self.assertEqual(jim.room, self.room3)

        # check modified contact
        ann = Contact.objects.get(uuid='C-001')
        self.assertEqual(ann.full_name, "Annie")
        self.assertEqual(ann.chat_name, "annie")
        self.assertEqual(ann.urn, 'tel:5678')
        self.assertEqual(ann.room, self.room2)

        # check deleted contact
        bob = Contact.objects.get(uuid='C-002')
        self.assertFalse(bob.is_active)
