from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dash.orgs.views import OrgCRUDL
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL


class OrgExtCRUDL(SmartCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit')
    model = Org

    class Create(OrgCRUDL.Create):
        pass

    class Update(OrgCRUDL.Update):
        pass

    class List(OrgCRUDL.List):
        pass

    class Home(OrgCRUDL.Home):
        fields = ('name', 'api_token', 'chat_name_field', 'new_contact_webhook', 'new_message_webhook')
        field_config = {'api_token': {'label': _("RapidPro API Token")}}
        permission = 'orgs.org_home'

        def derive_title(self):
            return _("My Organization")

        def get_chat_name_field(self, obj):
            return obj.get_chat_name_field()

        def get_new_contact_webhook(self, obj):
            url = reverse('api.temba_handler', kwargs=dict(entity='contact', action='new'))
            return self.request.build_absolute_uri('%s?token=%s&contact=@contact.uuid&group=[GROUP_UUID]' % (url, obj.get_secret_token()))

        def get_new_message_webhook(self, obj):
            url = reverse('api.temba_handler', kwargs=dict(entity='message', action='new'))
            return self.request.build_absolute_uri('%s?token=%s&contact=@contact.uuid&text=@step.value&group=[GROUP_UUID]' % (url, obj.get_secret_token()))

    class Edit(OrgCRUDL.Edit):
        permission = 'orgs.org_edit'
        success_url = '@orgs_ext.org_home'
