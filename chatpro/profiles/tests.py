from __future__ import unicode_literals

from chatpro.test import ChatProTest
from chatpro.profiles.models import Contact, Profile
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact


class UserPatchTest(ChatProTest):
    def test_has_profile(self):
        self.assertFalse(self.superuser.has_profile())
        self.assertTrue(self.admin.has_profile())
        self.assertTrue(self.user1.has_profile())

    def test_get_full_name(self):
        self.assertEqual(self.superuser.get_full_name(), "")
        self.assertEqual(self.admin.get_full_name(), "Richard")
        self.assertEqual(self.user1.get_full_name(), "Sam Sims")


class ContactTest(ChatProTest):
    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('chatpro.dash_ext.TembaClient.create_contact')
    def test_create(self, mock_create_contact):
        mock_create_contact.return_value = TembaContact.create(uuid='RRR-007', name="Mo Chats", urns=['tel:078123'],
                                                               groups=['000-007'], fields=dict(chat_name="momo"),
                                                               language='eng', modified_on=timezone.now())

        contact = Contact.create(self.unicef, self.user1, "Mo Chats", "momo", 'tel:078123', self.room1)

        self.assertEqual(contact.profile.full_name, "Mo Chats")
        self.assertEqual(contact.profile.chat_name, "momo")

        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.room, self.room1)
        self.assertEqual(contact.created_by, self.user1)
        self.assertIsNotNone(contact.created_on)
        self.assertEqual(contact.modified_by, self.user1)
        self.assertIsNotNone(contact.modified_on)

        # reload and check UUID was updated by push task
        contact = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact.uuid, 'RRR-007')

        self.assertEqual(mock_create_contact.call_count, 1)

    def test_from_temba(self):
        temba_contact = TembaContact.create(uuid='000-007', name="Jan", urns=['tel:123'],
                                            groups=['000-007'], fields=dict(chat_name="jxn"),
                                            language='eng', modified_on=timezone.now())

        contact = Contact.from_temba(self.unicef, self.room1, temba_contact)

        self.assertEqual(contact.profile.full_name, "Jan")
        self.assertEqual(contact.profile.chat_name, "jxn")

        self.assertEqual(contact.room, self.room1)
        self.assertEqual(contact.urn, 'tel:123')
        self.assertEqual(contact.uuid, '000-007')
        self.assertIsNone(contact.created_by)
        self.assertIsNotNone(contact.created_on)
        self.assertIsNone(contact.modified_by)
        self.assertIsNotNone(contact.modified_on)

    def test_to_temba(self):
        temba_contact = self.contact1.to_temba()
        self.assertEqual(temba_contact.name, "Ann")
        self.assertEqual(temba_contact.urns, ['tel:1234'])
        self.assertEqual(temba_contact.fields, {'chat_name': "ann"})
        self.assertEqual(temba_contact.groups, ['000-001'])
        self.assertEqual(temba_contact.uuid, '000-001')

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('chatpro.dash_ext.TembaClient.delete_contact')
    def test_release(self, mock_delete_contact):
        self.contact1.release()
        self.assertFalse(self.contact1.is_active)

        self.assertEqual(mock_delete_contact.call_count, 1)


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

    def test_unicode(self):
        self.assertEqual(unicode(self.user1.profile), "Sam Sims")
        self.user1.profile.full_name = None
        self.user1.profile.save()
        self.assertEqual(unicode(self.user1.profile), "sammy")
        self.user1.profile.chat_name = None
        self.user1.profile.save()
        self.assertEqual(unicode(self.user1.profile), "sam@unicef.org")

        self.assertEqual(unicode(self.contact1.profile), "Ann")
        self.contact1.profile.full_name = None
        self.contact1.profile.save()
        self.assertEqual(unicode(self.contact1.profile), "ann")
        self.contact1.profile.chat_name = None
        self.contact1.profile.save()
        self.assertEqual(unicode(self.contact1.profile), "1234")


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
        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('profiles.contact_update', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)

        data = dict(full_name="Morris", chat_name="momo2", phone="6789", room=self.room2.pk)
        response = self.url_post('unicef', reverse('profiles.contact_update', args=[self.contact1.pk]), data)
        self.assertEqual(response.status_code, 302)

        # check updated contact and profile
        contact = Contact.objects.get(pk=self.contact1.pk)
        self.assertEqual(contact.profile.full_name, "Morris")
        self.assertEqual(contact.profile.chat_name, "momo2")
        self.assertEqual(contact.urn, 'tel:6789')
        self.assertEqual(contact.room, self.room2)

    def test_list(self):
        url = reverse('profiles.contact_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

    def test_delete(self):
        # log in as an org administrator
        self.login(self.admin)

        # delete contact
        response = self.url_post('unicef', reverse('profiles.contact_delete', args=[self.contact1.pk]))
        self.assertRedirects(response, 'http://unicef.localhost/contact/')
        self.assertFalse(Contact.objects.get(pk=self.contact1.pk).is_active)

        # try to delete contact from other org
        response = self.url_post('unicef', reverse('profiles.contact_delete', args=[self.contact6.pk]))
        self.assertLoginRedirect(response, 'unicef', '/contact/delete/%d/' % self.contact6.pk)
        self.assertTrue(Contact.objects.get(pk=self.contact6.pk).is_active)

        # log in as user
        self.login(self.user1)

        # delete contact from room we manage
        response = self.url_post('unicef', reverse('profiles.contact_delete', args=[self.contact3.pk]))
        self.assertRedirects(response, 'http://unicef.localhost/contact/')
        contact = Contact.objects.get(pk=self.contact3.pk)
        self.assertFalse(contact.is_active)
        # self.assertEqual(contact.modified_by, self.user1)  # TODO re-enable with https://github.com/nyaruka/smartmin/pull/47

        # try to delete contact from room we don't manage
        response = self.url_post('unicef', reverse('profiles.contact_delete', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Contact.objects.get(pk=self.contact5.pk).is_active)


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
        url = reverse('profiles.user_update', args=[self.user1.pk])

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['form'].fields['rooms'].choices), 3)  # can assign to any org room
        self.assertEqual(len(response.context['form'].fields['manage_rooms'].choices), 3)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'chat_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')

        # submith with all fields entered
        data = dict(full_name="Morris", chat_name="momo2", email="mo2@chat.com",
                    rooms=[], manage_rooms=[self.room3.pk], is_active=True)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check updated user and profile
        user = User.objects.get(pk=self.user1.pk)
        self.assertEqual(user.profile.full_name, "Morris")
        self.assertEqual(user.profile.chat_name, "momo2")
        self.assertEqual(user.email, "mo2@chat.com")
        self.assertEqual(list(user.rooms.all()), [self.room3])
        self.assertEqual(list(user.manage_rooms.all()), [self.room3])

        # check de-activating user
        data = dict(full_name="Morris", chat_name="momo2", email="mo2@chat.com",
                    rooms=[], manage_rooms=[], is_active=False)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check user object is inactive
        user = User.objects.get(pk=self.user1.pk)
        self.assertFalse(user.is_active)

    def test_list(self):
        url = reverse('profiles.user_list')

        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_self(self):
        url = reverse('profiles.user_self')

        # try as unauthenticated
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

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


class ProfileCRUDLTest(ChatProTest):
    def test_read(self):
        # log in as an org administrator
        self.login(self.admin)

        # view our own profile
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('profiles.user_self'))

        # view other user's profile
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.user1.profile.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('profiles.user_update', args=[self.user1.pk]))

        # try to view user from other org
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.user3.profile.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user
        self.login(self.user1)

        # view other user's profile
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.admin.profile.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['edit_button_url'])

        # view contact in a room we manage
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.contact3.profile.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('profiles.contact_update', args=[self.contact3.pk]))

        # view contact in a room we don't manage
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.contact5.profile.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['edit_button_url'])

        # try to view contact from other org
        response = self.url_get('unicef', reverse('profiles.profile_read', args=[self.contact6.profile.pk]))
        self.assertEqual(response.status_code, 404)
