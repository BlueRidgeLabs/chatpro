from __future__ import absolute_import, unicode_literals

from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse
from mock import patch
from temba.types import Field as TembaField


class OrgExtCRUDLTest(ChatProTest):
    def test_home(self):
        url = reverse('orgs_ext.org_home')

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

    @patch('dash.orgs.models.TembaClient.get_fields')
    def test_edit(self, mock_get_fields):
        mock_get_fields.return_value = [TembaField.create(key='chat_name', label="Chat name", value_type='T')]

        url = reverse('orgs_ext.org_edit')

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
