from __future__ import absolute_import, unicode_literals

from chatpro.profiles.models import Contact
from chatpro.rooms.models import Room
from chatpro.test import ChatProTest
from django.utils import timezone
from django.test.utils import override_settings
from mock import patch
from temba.types import Contact as TembaContact
from .temba import temba_compare_contacts, temba_merge_contacts, temba_pull_contacts
from . import intersection, union


class InitTest(ChatProTest):
    def test_intersection(self):
        self.assertEqual(intersection(), [])
        self.assertEqual(intersection([1]), [1])
        self.assertEqual(sorted(intersection([1, 2, 3], [2, 3, 4])), [2, 3])

    def test_union(self):
        self.assertEqual(union(), [])
        self.assertEqual(union([1]), [1])
        self.assertEqual(sorted(union([1, 2, 3], [2, 3, 4])), [1, 2, 3, 4])


class TembaTest(ChatProTest):
    def test_compare_contacts(self):
        # no differences
        first = TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
                                    fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        second = TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
                                     fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertFalse(temba_compare_contacts(first, second))
        self.assertFalse(temba_compare_contacts(second, first))

        # different name
        second = TembaContact.create(uuid='000-001', name="Annie", urns=['tel:1234'], groups=['000-001'],
                                     fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertTrue(temba_compare_contacts(first, second))

        # different URNs
        second = TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234', 'twitter:ann'], groups=['000-001'],
                                     fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertTrue(temba_compare_contacts(first, second))

        # different group
        second = TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-002'],
                                     fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertTrue(temba_compare_contacts(first, second))

        # different field
        second = TembaContact.create(uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
                                     fields=dict(chat_name="annie"), language='eng', modified_on=timezone.now())
        self.assertTrue(temba_compare_contacts(first, second))

    def test_merge_contacts(self):
        contact1 = TembaContact.create(uuid="000-001", name="Bob",
                                       urns=['tel:123', 'email:bob@bob.com'],
                                       fields=dict(chat_name="bob", age=23),
                                       groups=['000-001', '000-008'])
        contact2 = TembaContact.create(uuid="000-001", name="Bobby",
                                       urns=['tel:234', 'twitter:bob'],
                                       fields=dict(chat_name="bobz", state='IN'),
                                       groups=['000-002', '000-003', '000-009'])

        merged = temba_merge_contacts(contact1, contact2, primary_groups=['000-001', '000-002', '000-003'])
        self.assertEqual(merged.uuid, '000-001')
        self.assertEqual(merged.name, "Bob")
        self.assertEqual(sorted(merged.urns), ['email:bob@bob.com', 'tel:123', 'twitter:bob'])
        self.assertEqual(merged.fields, dict(chat_name="bob", age=23, state='IN'))
        self.assertEqual(sorted(merged.groups), ['000-001', '000-008', '000-009'])

    @patch('chatpro.utils.temba.TembaClient.get_contacts')
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


class OrgPatchTest(ChatProTest):
    @override_settings(SITE_API_HOST='example.com')
    def test_get_temba_client(self):
        client = self.unicef.get_temba_client()
        self.assertEqual(client.token, self.unicef.api_token)
        self.assertEqual(client.root_url, 'https://example.com/api/v1')