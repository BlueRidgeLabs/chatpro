from __future__ import unicode_literals

from chatpro.test import ChatProTest
from chatpro.profiles.models import Profile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
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


class ProfileTest(ChatProTest):
    def test_create_admin(self):
        user = Profile.create_admin(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123")
        self.assertEqual(user.profile.full_name, "Mo Chats")
        self.assertEqual(user.profile.chat_name, "momo")

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "mo@chat.com")
        self.assertEqual(user.get_full_name(), "Mo Chats")

        self.assertEqual(user.rooms.count(), 0)
        self.assertEqual(user.manage_rooms.count(), 0)
        self.assertEqual(user.get_rooms(self.unicef).count(), 3)

        self.assertTrue(user.has_room_access(self.room1))
        self.assertTrue(user.has_room_access(self.room1, manage=True))
        self.assertTrue(user.has_room_access(self.room2))
        self.assertTrue(user.has_room_access(self.room2, manage=True))
        self.assertTrue(user.has_room_access(self.room3))
        self.assertTrue(user.has_room_access(self.room3, manage=True))
        self.assertFalse(user.has_room_access(self.room4))
        self.assertFalse(user.has_room_access(self.room4, manage=True))

    def test_create_user(self):
        user = Profile.create_user(self.unicef, "Mo Chats", "momo", "mo@chat.com", "Qwerty123",
                                   rooms=[self.room1], manage_rooms=[self.room2])
        self.assertEqual(user.profile.full_name, "Mo Chats")
        self.assertEqual(user.profile.chat_name, "momo")

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "mo@chat.com")
        self.assertEqual(user.get_full_name(), "Mo Chats")

        self.assertEqual(user.rooms.count(), 2)
        self.assertEqual(user.manage_rooms.count(), 1)
        self.assertEqual(user.get_rooms(self.unicef).count(), 2)

        self.assertTrue(user.has_room_access(self.room1))
        self.assertFalse(user.has_room_access(self.room1, manage=True))
        self.assertTrue(user.has_room_access(self.room2))
        self.assertTrue(user.has_room_access(self.room2, manage=True))
        self.assertFalse(user.has_room_access(self.room3))
        self.assertFalse(user.has_room_access(self.room3, manage=True))
        self.assertFalse(user.has_room_access(self.room4))
        self.assertFalse(user.has_room_access(self.room4, manage=True))

    def test_create_contact(self):
        contact = Profile.create_contact(self.unicef, "Mo Chats", "momo", 'tel:078123', self.room1, '000-007')
        self.assertEqual(contact.profile.full_name, "Mo Chats")
        self.assertEqual(contact.profile.chat_name, "momo")

        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.room, self.room1)
        self.assertEqual(contact.uuid, '000-007')


class ProfileCRUDLTest(ChatProTest):
    def test_create(self):
        create_url = reverse('profiles.profile_create')

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

        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        update_url = reverse('profiles.profile_update', args=[self.admin.pk])

        # log in as an org administrator
        self.login(self.admin)

        # TODO

    def test_users(self):
        list_url = reverse('profiles.profile_users')

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/profile/users/')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/profile/users/')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
