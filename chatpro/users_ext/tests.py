from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from chatpro.chat.models import RoomPermission
from chatpro.test import ChatProTest


class OrgTest(ChatProTest):
    @override_settings(SITE_API_HOST='example.com')
    def test_get_temba_client(self):
        client = self.unicef.get_temba_client()
        self.assertEqual(client.token, self.unicef.api_token)
        self.assertEqual(client.root_url, 'https://example.com/api/v1')


class UserTest(ChatProTest):
    def test_create(self):
        user = User.create(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123",
                           rooms=[self.room1], manage_rooms=[self.room2])
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "mo@chat.com")

        self.assertEqual(user.get_full_name(), "Mo Chats")
        self.assertEqual(user.profile.full_name, "Mo Chats")
        self.assertEqual(user.profile.chat_name, "momo")

        self.assertEqual(user.rooms.count(), 1)
        self.assertEqual(user.manage_rooms.count(), 1)
        self.assertEqual(user.get_all_rooms().count(), 2)

        self.assertTrue(user.has_room_perm(self.room1, RoomPermission.read))
        self.assertTrue(user.has_room_perm(self.room1, RoomPermission.send))
        self.assertFalse(user.has_room_perm(self.room1, RoomPermission.manage))
        self.assertTrue(user.has_room_perm(self.room2, RoomPermission.read))
        self.assertTrue(user.has_room_perm(self.room2, RoomPermission.send))
        self.assertTrue(user.has_room_perm(self.room2, RoomPermission.manage))
        self.assertFalse(user.has_room_perm(self.room3, RoomPermission.read))
        self.assertFalse(user.has_room_perm(self.room3, RoomPermission.send))
        self.assertFalse(user.has_room_perm(self.room3, RoomPermission.manage))


class AdministratorCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('users_ext.administrator_list')

        # log in as a non-superuser
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/administrator/')

        # log in as a superuser
        self.login(self.superuser)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class UserCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('users_ext.user_list')

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/user/')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/user/')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_create(self):
        create_url = reverse('users_ext.user_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit with no fields entered
        response = self.url_post('unicef', create_url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'chat_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password', 'This field is required.')

        # submit again with all required fields but invalid password
        data = dict(full_name="Mo Chats", chat_name="momo", email="mo@chat.com", password="123")
        response = self.url_post('unicef', create_url, data)
        self.assertFormError(response, 'form', 'password', 'Ensure this value has at least 8 characters (it has 3).')

        # submit again with valid password
        data = dict(full_name="Mo Chats", chat_name="momo", email="mo@chat.com", password="Qwerty123")
        response = self.url_post('unicef', create_url, data)

        user = User.objects.get(email="mo@chat.com")
        self.assertEqual(user.profile.full_name, "Mo Chats")
        self.assertEqual(user.profile.chat_name, "momo")

    def test_update(self):
        update_url = reverse('users_ext.user_update', args=[self.admin.pk])

        # log in as an org administrator
        self.login(self.admin)

        # TODO
