from __future__ import unicode_literals

from dash.orgs.models import Org
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from chatpro.chat.models import Contact, Room
from chatpro.test import ChatProTest
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class ContactTest(ChatProTest):
    def test_get_urn(self):
        self.assertEqual(self.contact1.get_urn(), ('tel', '1234'))
        self.assertEqual(self.contact4.get_urn(), ('twitter', 'danny'))


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


class RoomTest(ChatProTest):
    def test_get_all(self):
        self.assertEqual(len(Room.get_all(self.unicef)), 3)
        self.assertEqual(len(Room.get_all(self.nyaruka)), 1)

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('temba.TembaClient')
    def test_update_room_groups(self, MockTembaClient):
        Org.get_temba_client = lambda org: MockTembaClient

        MockTembaClient.get_groups.return_value = TembaGroup.deserialize_list([
            dict(uuid='000-101', name='New group', size=2)
        ])
        MockTembaClient.get_contacts.return_value = TembaContact.deserialize_list([
            dict(uuid='000-201', name="Jan", urns=['tel:123'], group_uuids=['000-101'], fields={}, language='eng', modified_on='2014-10-01T06:54:09.817Z'),
            dict(uuid='000-202', name="Ken", urns=['tel:234'], group_uuids=['000-101'], fields={}, language='eng', modified_on='2014-10-01T06:54:09.817Z')
        ])

        # select one new group
        Room.update_room_groups(self.unicef, ['000-001'])
        self.assertEqual(self.unicef.rooms.get(is_active=True).name, 'New group')
        self.assertEqual(self.unicef.rooms.filter(is_active=False).count(), 3)  # existing de-activated

        # check contact changes
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        self.assertEqual(self.unicef.contacts.filter(is_active=False).count(), 5)  # existing de-activated

        # change group and contacts on chatpro side
        Room.objects.filter(name="New group").update(name="Huh?", is_active=False)
        Contact.objects.filter(name="Jan").update(name="Janet")
        Contact.objects.filter(name="Ken").update(is_active=False)

        # re-select new group
        Room.update_room_groups(self.unicef, ['000-001'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.rooms.get(is_active=True).name, 'New group')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(name="Jan", is_active=True)


class RoomCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.room_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/room/')

        # log in as a non-administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)
