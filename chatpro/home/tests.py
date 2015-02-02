from __future__ import absolute_import, unicode_literals

from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse


class HomeViewTest(ChatProTest):
    def test_chat(self):
        # can't access it anonymously
        response = self.url_get('unicef', reverse('home.chat'))
        self.assertLoginRedirect(response, 'unicef', '/')

        # login as superuser
        self.login(self.superuser)

        # can access, but can't chat
        response = self.url_get('unicef', reverse('home.chat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['rooms']), 0)

        # login as administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('home.chat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['initial_room'], self.room3)  # first A-Z
        self.assertEqual([r.name for r in response.context['rooms']], ["Bags", "Bees", "Cars"])

        # login as regular user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('home.chat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['initial_room'], self.room2)
        self.assertEqual([r.name for r in response.context['rooms']], ["Bees", "Cars"])

        # specify initial room
        response = self.url_get('unicef', reverse('home.chat_in', args=[self.room2.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['initial_room'], self.room2)

        # try to specify an initial room we don't have access to
        response = self.url_get('unicef', reverse('home.chat_in', args=[self.room3.pk]))
        self.assertEqual(response.status_code, 403)
