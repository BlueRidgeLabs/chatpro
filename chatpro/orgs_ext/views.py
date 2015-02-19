from __future__ import absolute_import, unicode_literals

from chatpro.orgs_ext import TaskType
from dash.orgs.models import Org
from dash.orgs.views import OrgCRUDL, InferOrgMixin, OrgPermsMixin, SmartUpdateView
from dash.utils import ms_to_datetime
from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext_lazy as _
from smartmin.templatetags.smartmin import format_datetime
from smartmin.users.views import SmartCRUDL


def build_webhook(org, request, entity, action, params):
    url = reverse('api.temba_handler', kwargs=dict(entity=entity, action=action))
    url = request.build_absolute_uri('%s?token=%s&%s' % (url, org.get_secret_token(), params))
    return 'POST %s' % url


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
        fields = ('name', 'api_token', 'chat_name_field', 'last_contact_sync', 'new_message_webhook', 'new_contact_webhook', 'delete_contact_webhook')
        field_config = {'api_token': {'label': _("RapidPro API Token")}}
        permission = 'orgs.org_home'

        def derive_title(self):
            return _("My Organization")

        def get_chat_name_field(self, obj):
            return obj.get_chat_name_field()

        def get_last_contact_sync(self, obj):
            result = obj.get_task_result(TaskType.sync_contacts)
            if result:
                return "%s (%d created, %d updated, %d deleted, %d failed)" % (format_datetime(ms_to_datetime(result['time'])),
                                                                               result['counts']['created'],
                                                                               result['counts']['updated'],
                                                                               result['counts']['deleted'],
                                                                               result['counts']['failed'])
            else:
                return None

        def get_new_message_webhook(self, obj):
            return build_webhook(obj, self.request, 'message', 'new', 'contact=@contact.uuid&text=@step.value&group=[GROUP_UUID]')

        def get_new_contact_webhook(self, obj):
            return build_webhook(obj, self.request, 'contact', 'new', 'contact=@contact.uuid&group=[GROUP_UUID]')

        def get_delete_contact_webhook(self, obj):
            return build_webhook(obj, self.request, 'contact', 'del', 'contact=@contact.uuid')

    class Edit(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        class OrgForm(forms.ModelForm):
            secret_token = forms.CharField(label=_("Secret token"),
                                           help_text=_("Secret token for all calls from RapidPro."))

            chat_name_field = forms.ChoiceField(choices=(), label=_("Chat name field"),
                                                help_text=_("Contact field to use as the chat name."))

            def __init__(self, *args, **kwargs):
                org = kwargs.pop('org')
                super(OrgExtCRUDL.Edit.OrgForm, self).__init__(*args, **kwargs)

                field_choices = []
                for field in org.get_temba_client().get_fields():
                    field_choices.append((field.key, "%s (%s)" % (field.label, field.key)))

                self.fields['secret_token'].initial = org.get_secret_token()
                self.fields['chat_name_field'].choices = field_choices
                self.fields['chat_name_field'].initial = org.get_chat_name_field()

            class Meta:
                model = Org

        fields = ('name', 'secret_token', 'chat_name_field')
        form_class = OrgForm
        permission = 'orgs.org_edit'
        title = _("Edit My Organization")
        success_url = '@orgs_ext.org_home'

        def get_form_kwargs(self):
            kwargs = super(OrgExtCRUDL.Edit, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def pre_save(self, obj):
            from . import ORG_CONFIG_SECRET_TOKEN, ORG_CONFIG_CHAT_NAME_FIELD
            obj = super(OrgExtCRUDL.Edit, self).pre_save(obj)
            obj.set_config(ORG_CONFIG_SECRET_TOKEN, self.form.cleaned_data['secret_token'])
            obj.set_config(ORG_CONFIG_CHAT_NAME_FIELD, self.form.cleaned_data['chat_name_field'])
            return obj
