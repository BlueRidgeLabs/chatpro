from __future__ import absolute_import, unicode_literals

from chatpro.test import ChatProTest
from django.test.utils import override_settings
from temba.types import Contact as TembaContact
from .temba import temba_merge_contacts
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
    def test_merge_contacts(self):
        contact1 = TembaContact.create(uuid="000-001", name="Bob",
                                       urns=['tel:123', 'email:bob@bob.com'],
                                       fields=dict(chat_name="bob", age=23),
                                       groups=['000-001', '000-008'])
        contact2 = TembaContact.create(uuid="000-001", name="Bobby",
                                       urns=['tel:234', 'twitter:bob'],
                                       fields=dict(chat_name="bobz", state='IN'),
                                       groups=['000-002', '000-003', '000-009'])

        merged = temba_merge_contacts(self.unicef, contact1, contact2)
        self.assertEqual(merged.uuid, '000-001')
        self.assertEqual(merged.name, "Bob")
        self.assertEqual(sorted(merged.urns), ['email:bob@bob.com', 'tel:123', 'twitter:bob'])
        self.assertEqual(merged.fields, dict(chat_name="bob", age=23, state='IN'))
        self.assertEqual(sorted(merged.groups), ['000-001', '000-008', '000-009'])


class OrgPatchTest(ChatProTest):
    @override_settings(SITE_API_HOST='example.com')
    def test_get_temba_client(self):
        client = self.unicef.get_temba_client()
        self.assertEqual(client.token, self.unicef.api_token)
        self.assertEqual(client.root_url, 'https://example.com/api/v1')