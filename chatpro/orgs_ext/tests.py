from __future__ import absolute_import, unicode_literals

from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse


class OrgExtCRUDLTest(ChatProTest):
    def test_home(self):
        url = reverse('orgs_ext.org_home')

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

    def test_edit(self):
        url = reverse('orgs_ext.org_edit')

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
