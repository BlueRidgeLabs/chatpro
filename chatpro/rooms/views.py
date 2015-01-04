from __future__ import unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.db.models import Count
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartReadView, SmartListView
from smartmin.users.views import SmartFormView
from .models import Room


class RoomCRUDL(SmartCRUDL):
    model = Room
    actions = ('list', 'select', 'profiles')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')

        def get_queryset(self, **kwargs):
            qs = super(RoomCRUDL.List, self).get_queryset(**kwargs)

            org = self.request.user.get_org()
            return qs.filter(org=org, is_active=True).order_by('name').annotate(num_contacts=Count('contacts'))

        def get_contacts(self, obj):
            return obj.num_contacts

    class Select(OrgPermsMixin, SmartFormView):
        class GroupsForm(forms.Form):
            groups = forms.MultipleChoiceField(choices=(), label=_("Groups"),
                                               help_text=_("Contact groups to be used as chat rooms"))

            def __init__(self, *args, **kwargs):
                org = kwargs['org']
                del kwargs['org']
                super(RoomCRUDL.Select.GroupsForm, self).__init__(*args, **kwargs)

                choices = []
                for group in org.get_temba_client().get_groups():
                    choices.append((group.uuid, "%s (%d)" % (group.name, group.size)))

                self.fields['groups'].choices = choices
                self.fields['groups'].initial = [room.group_uuid for room in org.rooms.filter(is_active=True)]


        title = _("Room Groups")
        form_class = GroupsForm
        success_url = '@rooms.room_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as chat rooms")

        def get_form_kwargs(self):
            kwargs = super(RoomCRUDL.Select, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def form_valid(self, form):
            Room.update_room_groups(self.request.user.get_org(), form.cleaned_data['groups'])
            return HttpResponseRedirect(self.get_success_url())

    class Profiles(OrgPermsMixin, SmartReadView):
        def get_context_data(self, **kwargs):
            context = super(RoomCRUDL.Profiles, self).get_context_data(**kwargs)

            context['contacts'] = self.object.get_contacts().select_related('profile')
            context['users'] = self.object.get_all_users().select_related('profile')
            return context

        def render_to_response(self, context, **response_kwargs):
            results = [c.profile.as_json() for c in context['contacts']]
            results += [u.profile.as_json() for u in context['users']]

            return JsonResponse({'count': len(results), 'results': results})
