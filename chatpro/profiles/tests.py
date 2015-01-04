from __future__ import unicode_literals

from chatpro.test import ChatProTest
from chatpro.profiles.models import Contact, Profile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from temba.types import Contact as TembaContact


class ContactTest(ChatProTest):
    def test_create(self):
        contact = Contact.create(self.unicef, "Mo Chats", "momo", 'tel:078123', self.room1, '000-007')
        self.assertEqual(contact.profile.full_name, "Mo Chats")
        self.assertEqual(contact.profile.chat_name, "momo")

        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.room, self.room1)
        self.assertEqual(contact.uuid, '000-007')

    def test_from_temba(self):
        temba_contact = TembaContact.deserialize(dict(uuid='000-007', name="Jan", urns=['tel:123'],
                                                      group_uuids=['000-007'], fields=dict(chat_name="jxn"),
                                                      language='eng', modified_on='2014-10-01T06:54:09.817Z'))
        contact = Contact.from_temba(self.unicef, self.room1, temba_contact)
        self.assertEqual(contact.profile.full_name, "Jan")
        self.assertEqual(contact.profile.chat_name, "jxn")
        self.assertEqual(contact.room, self.room1)
        self.assertEqual(contact.urn, 'tel:123')
        self.assertEqual(contact.uuid, '000-007')

    def test_to_temba(self):
        temba_contact = self.contact1.to_temba()
        self.assertEqual(temba_contact.name, "Ann")
        self.assertEqual(temba_contact.urns, ['tel:1234'])
        self.assertEqual(temba_contact.fields, {'chat_name': "ann"})
        self.assertEqual(temba_contact.group_uuids, ['000-001'])


class ProfileTest(ChatProTest):
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


class ContactCRUDLTest(ChatProTest):
    def test_create(self):
        url = reverse('profiles.contact_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'chat_name', 'This field is required.')
        self.assertFormError(response, 'form', 'phone', 'This field is required.')
        self.assertFormError(response, 'form', 'room', 'This field is required.')

        # submit again with all fields
        data = dict(full_name="Mo Chats", chat_name="momo", phone="5678", room=self.room1.pk)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check new contact and profile
        contact = Contact.objects.get(urn='tel:5678')
        self.assertEqual(contact.profile.full_name, "Mo Chats")
        self.assertEqual(contact.profile.chat_name, "momo")
        self.assertEqual(contact.room, self.room1)

    def test_update(self):
        # TODO
        pass

    def test_list(self):
        url = reverse('profiles.contact_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)


class UserCRUDLTest(ChatProTest):
    def test_create(self):
        url = reverse('profiles.user_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'chat_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password', 'This field is required.')

        # submit again with all required fields but invalid password
        data = dict(full_name="Mo Chats", chat_name="momo", email="mo@chat.com", password="123")
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', 'password', 'Ensure this value has at least 8 characters (it has 3).')

        # submit again with valid password
        data = dict(full_name="Mo Chats", chat_name="momo", email="mo@chat.com", password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check new user and profile
        user = User.objects.get(email="mo@chat.com")
        self.assertEqual(user.profile.full_name, "Mo Chats")
        self.assertEqual(user.profile.chat_name, "momo")

    def test_update(self):
        # TODO
        pass

    def test_list_users(self):
        list_url = reverse('profiles.user_list')

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


class ProfileCRUDLTest(ChatProTest):
    def test_read(self):
        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)

    def test_self(self):
        url = reverse('profiles.profile_self')

        # try as unauthenticated
        response = self.url_get('unicef', url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/profile/self/')

        # try as superuser (doesn't have a chat profile)
        self.login(self.superuser)
        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 404)

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
