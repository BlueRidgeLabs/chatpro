from __future__ import unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.test import TestCase
from chatpro.chat.models import Contact, Room
from uuid import uuid4


class ChatProTest(TestCase):
    """
    Base class for all test cases in ChatPro
    """
    def setUp(self):
        self.superuser = User.objects.create_superuser(username="super", email="super@user.com", password="super")

        self.unicef = self.create_org("UNICEF", timezone="Asia/Kabul", subdomain="unicef")
        self.nyaruka = self.create_org("Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka")

        self.admin = self.create_administrator(self.unicef, "Richard", "admin", "admin@unicef.org")
        self.nic = self.create_administrator(self.nyaruka, "Nicholas", "nic", "nic@nyaruka.com")

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

        self.contact1 = self.create_contact(self.unicef, "Ann", "tel:1234", self.room1, '000-001')
        self.contact2 = self.create_contact(self.unicef, "Bob", "tel:2345", self.room1, '000-002')
        self.contact3 = self.create_contact(self.unicef, "Cat", "tel:3456", self.room2, '000-003')
        self.contact4 = self.create_contact(self.unicef, "Dan", "twitter:danny", self.room2, '000-004')
        self.contact5 = self.create_contact(self.unicef, "Eve", "tel:5567", self.room3, '000-005')

    def create_org(self, name, timezone, subdomain):
        return Org.objects.create(name=name, timezone=timezone, subdomain=subdomain, api_token=unicode(uuid4()),
                                  created_by=self.superuser, modified_by=self.superuser)

    def create_administrator(self, org, full_name, chat_name, email):
        return User.create_administrator(org, full_name, chat_name, email, password=email)

    def create_user(self, org, full_name, chat_name, email, rooms, manage_rooms):
        return User.create(org, full_name, chat_name, email, password=email, rooms=rooms, manage_rooms=manage_rooms)

    def create_room(self, org, name, group_uuid):
        return Room.create(org, name, group_uuid)

    def create_contact(self, org, name, urn, room, uuid):
        return Contact.create(org, name, urn, room, uuid)

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
