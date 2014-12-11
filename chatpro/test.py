from __future__ import unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User as AuthUser
from django.test import TestCase
from chatpro.chat.models import Contact, Room, User
from uuid import uuid4


class ChatProTest(TestCase):
    """
    Base class for all test cases in ChatPro
    """
    def setUp(self):
        self.superuser = AuthUser.objects.create_superuser(username="super", email="super@user.com", password="super")

        self.unicef = Org.objects.create(name="UNICEF", timezone="Asia/Kabul", subdomain="unicef",
                                         created_by=self.superuser, modified_by=self.superuser)
        self.nyaruka = Org.objects.create(name="Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka",
                                          created_by=self.superuser, modified_by=self.superuser)

        self.admin = self.create_administator(self.unicef, "admin", first_name="Richard", last_name="Admin")
        self.nic = self.create_administator(self.nyaruka, "nic")

        # create some chat rooms
        self.room1 = self.create_room(self.unicef, "Cars")
        self.room2 = self.create_room(self.unicef, "Bees")
        self.room3 = self.create_room(self.unicef, "Bags")
        self.room4 = self.create_room(self.nyaruka, "Code")

        # create some room users and managers
        self.user1 = self.create_chatuser(self.unicef, "Sam Sims", "sammy", "sam@unicef.org",
                                          rooms=[self.room1], manage_rooms=[self.room2])
        self.user2 = self.create_chatuser(self.unicef, "Sue", "sue80", "sue@unicef.org",
                                          rooms=[self.room2, self.room3], manage_rooms=[])
        self.user3 = self.create_chatuser(self.nyaruka, "Eric", "newcomer", "eric@nyaruka.com",
                                          rooms=[], manage_rooms=[self.room4])

        self.create_contact(self.unicef, "Ann", "1234", self.room1)
        self.create_contact(self.unicef, "Bob", "2345", self.room1)
        self.create_contact(self.unicef, "Cat", "3456", self.room2)
        self.create_contact(self.unicef, "Dan", "4567", self.room2)
        self.create_contact(self.unicef, "Eve", "5567", self.room3)

    def create_administator(self, org, username, **extra_fields):
        user = self.create_authuser(org, username, **extra_fields)
        org.administrators.add(user)
        return user

    def create_chatuser(self, org, name, chatname, email, rooms, manage_rooms):
        return User.create(org, name, chatname, email, email, rooms, manage_rooms)

    def create_authuser(self, org, username, **extra_fields):
        user = AuthUser.objects.create_user(username, "%s@nyaruka.com" % username, username, **extra_fields)
        user.set_org(org)
        return user

    def create_room(self, org, name, group_uuid=None):
        if not group_uuid:
            group_uuid = unicode(uuid4())

        return Room.create(org, name, group_uuid)

    def create_contact(self, org, name, phone, room, uuid=None):
        if not uuid:
            uuid = unicode(uuid4())

        return Contact.create(org, name, 'tel:%s' % phone, room, uuid)

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
