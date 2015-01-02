from __future__ import unicode_literals

from chatpro.test import ChatProTest
from chatpro.profiles.models import Profile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings


class OrgTest(ChatProTest):
    @override_settings(SITE_API_HOST='example.com')
    def test_get_temba_client(self):
        client = self.unicef.get_temba_client()
        self.assertEqual(client.token, self.unicef.api_token)
        self.assertEqual(client.root_url, 'https://example.com/api/v1')


class ProfileTest(ChatProTest):
    def test_create_administrator(self):
        profile = Profile.create_administrator(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123")
        self.assertEqual(profile.full_name, "Mo Chats")
        self.assertEqual(profile.chat_name, "momo")

        self.assertEqual(profile.user.first_name, "")
        self.assertEqual(profile.user.last_name, "")
        self.assertEqual(profile.user.email, "mo@chat.com")
        self.assertEqual(profile.user.get_full_name(), "Mo Chats")

        self.assertEqual(profile.user.rooms.count(), 0)
        self.assertEqual(profile.user.manage_rooms.count(), 0)
        self.assertEqual(profile.user.get_all_rooms().count(), 3)

        self.assertTrue(profile.user.has_room_access(self.room1))
        self.assertTrue(profile.user.has_room_access(self.room1, manage=True))
        self.assertTrue(profile.user.has_room_access(self.room2))
        self.assertTrue(profile.user.has_room_access(self.room2, manage=True))
        self.assertTrue(profile.user.has_room_access(self.room3))
        self.assertTrue(profile.user.has_room_access(self.room3, manage=True))
        self.assertFalse(profile.user.has_room_access(self.room4))
        self.assertFalse(profile.user.has_room_access(self.room4, manage=True))

    def test_create_user(self):
        profile = Profile.create_user(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123",
                                      rooms=[self.room1], manage_rooms=[self.room2])
        self.assertEqual(profile.full_name, "Mo Chats")
        self.assertEqual(profile.chat_name, "momo")

        self.assertEqual(profile.user.first_name, "")
        self.assertEqual(profile.user.last_name, "")
        self.assertEqual(profile.user.email, "mo@chat.com")
        self.assertEqual(profile.user.get_full_name(), "Mo Chats")

        self.assertEqual(profile.user.rooms.count(), 1)
        self.assertEqual(profile.user.manage_rooms.count(), 1)
        self.assertEqual(profile.user.get_all_rooms().count(), 2)

        self.assertTrue(profile.user.has_room_access(self.room1))
        self.assertFalse(profile.user.has_room_access(self.room1, manage=True))
        self.assertTrue(profile.user.has_room_access(self.room2))
        self.assertTrue(profile.user.has_room_access(self.room2, manage=True))
        self.assertFalse(profile.user.has_room_access(self.room3))
        self.assertFalse(profile.user.has_room_access(self.room3, manage=True))
        self.assertFalse(profile.user.has_room_access(self.room4))
        self.assertFalse(profile.user.has_room_access(self.room4, manage=True))

    def test_create_contact(self):
        profile = Profile.create_contact(self.unicef, "Mo Chats", "momo", 'tel:078123', self.room1, '000-007')
        self.assertEqual(profile.full_name, "Mo Chats")
        self.assertEqual(profile.chat_name, "momo")

        self.assertEqual(profile.contact.urn, 'tel:078123')
        self.assertEqual(profile.contact.room, self.room1)
        self.assertEqual(profile.contact.uuid, '000-007')


class ProfileCRUDLTest(ChatProTest):
    def test_create(self):
        create_url = reverse('users_ext.profile_create')

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

    def test_read(self):
        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('users_ext.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('users_ext.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        update_url = reverse('users_ext.profile_update', args=[self.admin.pk])

        # log in as an org administrator
        self.login(self.admin)

        # TODO

    def test_list(self):
        list_url = reverse('users_ext.profile_list')

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/profile/')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/profile/')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
