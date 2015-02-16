from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartReadView, SmartListView
from smartmin.users.views import SmartFormView
from .models import Room


class RoomCRUDL(SmartCRUDL):
    model = Room
    actions = ('read', 'list', 'select', 'participants')

    class Read(OrgObjPermsMixin, SmartReadView):
        fields = ('contacts', 'messages', 'last_active', 'managers')

        def get_queryset(self):
            return self.request.user.get_rooms(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(RoomCRUDL.Read, self).get_context_data(**kwargs)
            context['user_can_manage'] = self.request.user.has_room_access(self.object, manage=True)
            return context

        def get_contacts(self, obj):
            return obj.get_contacts().count()

        def get_messages(self, obj):
            return obj.messages.count()

        def get_last_active(self, obj):
            last_msg = obj.messages.order_by('-time').first()
            return last_msg.time if last_msg else _("Never")

        def get_managers(self, obj):
            return ",".join([unicode(m) for m in obj.get_managers()])

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')
        default_order = ('name',)

        def derive_queryset(self, **kwargs):
            return Room.get_all(self.request.user.get_org())

        def get_contacts(self, obj):
            return obj.get_contacts().count()

    class Select(OrgPermsMixin, SmartFormView):
        class GroupsForm(forms.Form):
            groups = forms.MultipleChoiceField(choices=(), label=_("Groups"),
                                               help_text=_("Contact groups to be used as chat rooms."))

            def __init__(self, *args, **kwargs):
                org = kwargs['org']
                del kwargs['org']
                super(RoomCRUDL.Select.GroupsForm, self).__init__(*args, **kwargs)

                choices = []
                for group in org.get_temba_client().get_groups():
                    choices.append((group.uuid, "%s (%d)" % (group.name, group.size)))

                self.fields['groups'].choices = choices
                self.fields['groups'].initial = [room.uuid for room in org.rooms.filter(is_active=True)]

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

    class Participants(OrgPermsMixin, SmartReadView):
        def get_queryset(self):
            return self.request.user.get_rooms(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(RoomCRUDL.Participants, self).get_context_data(**kwargs)

            context['contacts'] = self.object.get_contacts().order_by('full_name')
            context['users'] = self.object.get_users().order_by('profile__full_name')
            return context

        def render_to_response(self, context, **response_kwargs):
            results = [c.as_participant_json() for c in context['contacts']]
            results += [u.profile.as_participant_json() for u in context['users']]

            return JsonResponse({'count': len(results), 'results': results})
