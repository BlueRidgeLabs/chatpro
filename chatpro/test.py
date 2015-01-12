from __future__ import unicode_literals

from chatpro.rooms.models import Room
from chatpro.profiles.models import Contact, Profile
from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.test import TestCase
from uuid import uuid4


class ChatProTest(TestCase):
    """
    Base class for all test cases in ChatPro
    """
    def setUp(self):
        self.superuser = User.objects.create_superuser(username="super", email="super@user.com", password="super")

        self.unicef = self.create_org("UNICEF", timezone="Asia/Kabul", subdomain="unicef")
        self.nyaruka = self.create_org("Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka")

        self.admin = self.create_admin(self.unicef, "Richard", "richard", "admin@unicef.org")
        self.nic = self.create_admin(self.nyaruka, "Nicholas", "nic", "nic@nyaruka.com")

        # create some chat rooms
        self.room1 = self.create_room(self.unicef, "Cars", '000-001')
        self.room2 = self.create_room(self.unicef, "Bees", '000-002')
        self.room3 = self.create_room(self.unicef, "Bags", '000-003')
        self.room4 = self.create_room(self.nyaruka, "Code", '000-004')

        # create some room users and managers
        self.user1 = self.create_user(self.unicef, "Sam Sims", "sammy", "sam@unicef.org",
                                      rooms=[self.room1], manage_rooms=[self.room2])
        self.user2 = self.create_user(self.unicef, "Sue", "sue80", "sue@unicef.org",
                                      rooms=[self.room2, self.room3], manage_rooms=[])
        self.user3 = self.create_user(self.nyaruka, "Eric", "newcomer", "eric@nyaruka.com",
                                      rooms=[], manage_rooms=[self.room4])

        self.contact1 = self.create_contact(self.unicef, "Ann", "ann", "tel:1234", self.room1, '000-001')
        self.contact2 = self.create_contact(self.unicef, "Bob", "bob", "tel:2345", self.room1, '000-002')
        self.contact3 = self.create_contact(self.unicef, "Cat", "cat", "tel:3456", self.room2, '000-003')
        self.contact4 = self.create_contact(self.unicef, "Dan", "dan", "twitter:danny", self.room2, '000-004')
        self.contact5 = self.create_contact(self.unicef, "Eve", "eve", "twitter:evee", self.room3, '000-005')
        self.contact6 = self.create_contact(self.nyaruka, "Bosco", "bosco", 'tel:07899', self.room4, '000-006')

    def create_org(self, name, timezone, subdomain):
        org = Org.objects.create(name=name, timezone=timezone, subdomain=subdomain, api_token=unicode(uuid4()),
                                 created_by=self.superuser, modified_by=self.superuser)
        org.set_config('secret_token', '1234567890')
        org.set_config('chat_name_field', 'chat_name')
        return org

    def create_room(self, org, name, uuid):
        return Room.create(org, name, uuid)

    def create_admin(self, org, full_name, chat_name, email):
        user = User.create(None, full_name, chat_name, email, password=email)
        user.org_admins.add(org)
        return user

    def create_user(self, org, full_name, chat_name, email, rooms, manage_rooms):
        return User.create(org, full_name, chat_name, email, password=email, rooms=rooms, manage_rooms=manage_rooms)

    def create_contact(self, org, full_name, chat_name, urn, room, uuid):
        user = org.administrators.first()
        return Contact.create(org, user, full_name, chat_name, urn, room, uuid)

    def login(self, user):
        result = self.client.login(username=user.username, password=user.username)
        self.assertTrue(result, "Couldn't login as %(user)s / %(user)s" % dict(user=user.username))

    def url_get(self, subdomain, url, params=None):
        if params is None:
            params = {}
        extra = {}
        if subdomain:
            extra['HTTP_HOST'] = '%s.localhost' % subdomain
        return self.client.get(url, params, **extra)

    def url_post(self, subdomain, url, data=None):
        if data is None:
            data = {}
        extra = {}
        if subdomain:
            extra['HTTP_HOST'] = '%s.localhost' % subdomain
        return self.client.post(url, data, **extra)

    def assertLoginRedirect(self, response, subdomain, next):
        self.assertRedirects(response, 'http://%s.localhost/users/login/?next=%s' % (subdomain, next))
