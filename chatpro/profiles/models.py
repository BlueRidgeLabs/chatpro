from __future__ import unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact who is tied to a single room
    """
    uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='contacts')

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='contacts',
                             help_text=_("Room which this contact belongs in"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    is_active = models.BooleanField(default=True, help_text="Whether this contact is active")

    def get_urn(self):
        return tuple(self.urn.split(':', 1))


class Profile(models.Model):
    """
    A user or contact who can participate in chat rooms
    """
    user = models.OneToOneField(User, null=True)

    contact = models.OneToOneField(Contact, null=True)

    full_name = models.CharField(verbose_name=_("Full name"), max_length=128, null=True)

    chat_name = models.CharField(verbose_name=_("Chat name"), max_length=16, null=True,
                                 help_text=_("Shorter name used for chat messages"))

    @classmethod
    def create_admin(cls, org, full_name, chat_name, email, password):
        """
        Creates an admin user with access to all rooms
        """
        user, profile = cls._create_base_user(full_name, chat_name, email, password)

        # setup as org admin
        if org:
            user.org_admins.add(org)
        return user

    @classmethod
    def create_user(cls, org, full_name, chat_name, email, password, rooms=(), manage_rooms=()):
        """
        Creates a regular user with specific room-level permissions
        """
        user, profile = cls._create_base_user(full_name, chat_name, email, password)

        # setup as org supervisor
        user.org_editors.add(org)
        user.rooms.add(*rooms)
        user.manage_rooms.add(*manage_rooms)
        return user

    @classmethod
    def _create_base_user(cls, full_name, chat_name, email, password):
        # create auth user
        user = User.objects.create(is_active=True, username=email, email=email)
        user.set_password(password)
        user.save()

        # add profile
        profile = cls.objects.create(user=user, full_name=full_name, chat_name=chat_name)
        return user, profile

    @classmethod
    def create_contact(cls, org, full_name, chat_name, urn, room, uuid):
        if org.id != room.org_id:
            raise ValueError("Room does not belong to org")

        # create contact
        contact = Contact.objects.create(org=org, urn=urn, room=room, uuid=uuid)

        # add profile
        cls.objects.create(contact=contact, full_name=full_name, chat_name=chat_name)
        return contact

    @classmethod
    def from_temba(cls, org, room, temba_contact):
        full_name = temba_contact.name
        chat_name = temba_contact.fields.get(org.get_chat_name_field(), None)
        urn = temba_contact.urns[0]
        return cls.create_contact(org, full_name, chat_name, urn, room, temba_contact.uuid)

    def is_contact(self):
        return bool(self.contact_id)

    def is_user(self):
        return bool(self.user_id)

    def as_json(self):
        _type = 'C' if self.is_contact() else 'U'

        return dict(id=self.user_id, type=_type, full_name=self.full_name, chat_name=self.chat_name)

    def __unicode__(self):
        if self.full_name:
            return self.full_name
        elif self.chat_name:
            return self.chat_name
        elif self.is_contact():
            return self.contact.get_urn()[1]
        else:
            return self.user.email
