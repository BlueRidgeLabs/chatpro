from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from chatpro.test import ChatProTest


class ContactTest(ChatProTest):
    # TODO
    pass


class ContactCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.contact_list')

        # log in as an administrator
        self.login(self.admin)

        # so should see contacts from all rooms
        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

        # log in as a supervisor for room #1 and #2
        self.login(self.supervisor1)

        # so should see contacts from just those rooms
        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)

        # log in as administrator for different org with no contacts
        self.login(self.nic)
        response = self.url_get('nyaruka', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)


class SupervisorCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.supervisor_list')

        # TODO fix problem with login template and re-enable

        #response = self.client_get(list_url)
        #self.assertRedirects(response, '/login')

        # log in as a supervisor
        #self.login(self.supervisor1)

        #response = self.client_get(list_url)
        #self.assertRedirects(response, '/login')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_create(self):
        create_url = reverse('chat.supervisor_create')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_post('unicef', create_url, dict(name="Shirley"))
        self.assertEqual(response.status_code, 400)
