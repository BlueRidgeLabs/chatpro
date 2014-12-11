from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from chatpro.chat.models import User
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

        # log in as a user of room #1 and #2
        self.login(self.user1)

        # so should see contacts from just those rooms
        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)

        # log in as administrator for different org with no contacts
        self.login(self.nic)
        response = self.url_get('nyaruka', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)


class UserTest(ChatProTest):
    def test_create(self):
        user = User.create(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123",
                           rooms=[self.room1], manage_rooms=[self.room2, self.room3])
        self.assertEqual(user.name, "Mo Chats")
        self.assertEqual(user.chatname, "momo")
        self.assertEqual(user.email, "mo@chat.com")
        self.assertEqual(user.rooms.count(), 1)
        self.assertEqual(user.manage_rooms.count(), 2)


class UserCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.user_list')

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
        create_url = reverse('chat.user_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit with no fields entered
        response = self.url_post('unicef', create_url, dict())
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        self.assertFormError(response, 'form', 'chatname', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password', 'This field is required.')

        # submit again with all required fields but invalid password
        data = dict(name="Mo Chats", chatname="momo", email="mo@chat.com", password="123")
        response = self.url_post('unicef', create_url, data)
        self.assertFormError(response, 'form', 'password', 'Ensure this value has at least 8 characters (it has 3).')

        # submit again with valid password
        data = dict(name="Mo Chats", chatname="momo", email="mo@chat.com", password="Qwerty123")
        response = self.url_post('unicef', create_url, data)

        user = User.objects.get(email="mo@chat.com")
        self.assertEqual(user.name, "Mo Chats")
        self.assertEqual(user.chatname, "momo")
