from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User)

    full_name = models.CharField(verbose_name=_("Full name"), max_length=128,
                                 help_text=_("The full name of this user"))

    chat_name = models.CharField(verbose_name=_("Chat name"), max_length=16,
                                 help_text=_("The chat name of this user"))

    def as_json(self):
        return dict(id=self.pk, type='U', full_name=self.full_name, chat_name=self.chat_name)

