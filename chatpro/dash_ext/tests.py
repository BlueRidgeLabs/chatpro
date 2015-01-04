from __future__ import unicode_literals

from chatpro.test import ChatProTest
from django.test.utils import override_settings


class UserTest(ChatProTest):
    def test_is_admin_for(self):
        self.assertTrue(self.admin.is_admin_for(self.unicef))
        self.assertFalse(self.admin.is_admin_for(self.nyaruka))
        self.assertFalse(self.user1.is_admin_for(self.unicef))


class OrgTest(ChatProTest):
    @override_settings(SITE_API_HOST='example.com')
    def test_get_temba_client(self):
        client = self.unicef.get_temba_client()
        self.assertEqual(client.token, self.unicef.api_token)
        self.assertEqual(client.root_url, 'https://example.com/api/v1')