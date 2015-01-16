from __future__ import unicode_literals

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

        # login as regular user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('home.chat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['initial_room'], self.room1)
        self.assertEqual(len(response.context['rooms']), 2)
        self.assertEqual(response.context['rooms'][0], self.room1)
        self.assertEqual(response.context['rooms'][1], self.room2)

        # specify initial room
        response = self.url_get('unicef', reverse('home.chat_in', args=[self.room2.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['initial_room'], self.room2)