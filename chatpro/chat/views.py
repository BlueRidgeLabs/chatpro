from __future__ import unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartReadView, SmartUpdateView, SmartListView
from smartmin.users.views import SmartFormView, SmartTemplateView
from .models import Contact, Room, Message
from .utils import parse_iso8601


class ContactForm(forms.ModelForm):
    name = forms.CharField(max_length=255, label=_("Name"), help_text=_("The full name of the contact."))

    phone = forms.CharField(max_length=255, label=_("Phone"), help_text=_("The phone number of the contact."))

    room = forms.ModelChoiceField(label=_("Room"), queryset=Room.objects.filter(pk=-1),
                                  required=False,
                                  help_text=_("The chat rooms which this user can chat in."))

    comment = forms.CharField(max_length=1000, label=_("Notes"), widget=forms.Textarea,
                              help_text=_("Additional information about this contact."))

    def __init__(self, *args, **kwargs):
        user = kwargs['user']
        del kwargs['user']
        super(ContactForm, self).__init__(*args, **kwargs)

        if user.is_administrator():
            self.fields['room'].queryset = Room.objects.filter(org=user.get_org()).order_by('name')
        else:
            self.fields['room'].queryset = user.get_rooms()

    class Meta:
        model = Contact


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('create', 'read', 'update', 'list', 'filter')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = ContactForm
        fields = ('room', 'name', 'phone')

        def get_form_kwargs(self):
            kwargs = super(ContactCRUDL.Create, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def pre_save(self, obj):
            obj = super(ContactCRUDL.Create, self).pre_save(obj)
            obj.org = self.request.user.get_org()
            obj.urn = 'tel:%s' % self.form.cleaned_data['phone']
            return obj

    class Read(OrgPermsMixin, SmartReadView):
        fields = ('room', 'name', 'phone', 'comment', 'last_seen')

        def get_last_seen(self, obj):
            last_msg = Message.objects.filter(contact_id=obj.pk).order_by('-time').first()
            return last_msg.time if last_msg else None

    class Update(OrgPermsMixin, SmartUpdateView):
        form_class = ContactForm
        fields = ('name', 'room', 'phone', 'comment')

        def get_form_kwargs(self):
            kwargs = super(ContactCRUDL.Update, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def derive_initial(self):
            initial = super(ContactCRUDL.Update, self).derive_initial()
            initial['phone'] = self.object.get_urn()[1]
            return initial

        def pre_save(self, obj):
            obj = super(ContactCRUDL.Update, self).pre_save(obj)
            obj.urn = 'tel:%s' % self.form.cleaned_data['phone']
            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'room', 'phone')
        link_fields = ('name', 'room')

        def get_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).get_queryset(**kwargs)

            org = self.request.user.get_org()
            qs = qs.filter(org=org, is_active=True).order_by('name')

            rooms = self.request.user.get_all_rooms()
            if rooms is not None:
                qs = qs.filter(room__in=rooms)
            return qs

        def lookup_field_link(self, context, field, obj):
            if field == 'room':
                return reverse('chat.contact_filter', args=[obj.room.pk])

            return super(ContactCRUDL.List, self).lookup_field_link(context, field, obj)

        def get_phone(self, obj):
            return obj.get_urn()[1]

    class Filter(OrgPermsMixin, SmartListView):
        fields = ('name', 'phone')
        default_order = ('name',)

        def derive_queryset(self, **kwargs):
            room = self.derive_room()
            return Contact.objects.filter(room=room, is_active=True, org=self.request.user.get_org())

        def get_phone(self, obj):
            return obj.get_urn()[1]

        def derive_room(self):
            if not hasattr(self, '_room'):
                self._room = Room.objects.get(pk=self.kwargs['room'])
            return self._room

        def derive_title(self):
            return _("Contacts in %s") % self.derive_room().name

        def get_context_data(self, *args, **kwargs):
            context = super(ContactCRUDL.Filter, self).get_context_data(**kwargs)
            room = self.derive_room()
            context['room'] = room
            return context

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<room>\d+)/$' % (path, action)


class RoomCRUDL(SmartCRUDL):
    model = Room
    actions = ('list', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name',)

        def get_queryset(self, **kwargs):
            qs = super(RoomCRUDL.List, self).get_queryset(**kwargs)

            org = self.request.user.get_org()
            return qs.filter(org=org, is_active=True).order_by('name')

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
        success_url = '@chat.room_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as chat rooms")

        def get_form_kwargs(self):
            kwargs = super(RoomCRUDL.Select, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def form_valid(self, form):
            org = self.request.user.get_org()
            org.update_room_groups(form.cleaned_data['groups'])
            return HttpResponseRedirect(self.get_success_url())


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send')

    class Send(OrgPermsMixin, SmartFormView):
        class SendForm(forms.ModelForm):
            room = forms.ModelChoiceField(queryset=Room.objects.filter(pk=-1))

            def __init__(self, *args, **kwargs):
                user = kwargs['user']
                del kwargs['user']
                super(MessageCRUDL.Send.SendForm, self).__init__(*args, **kwargs)

                self.fields['room'].queryset = user.get_all_rooms().order_by('name')

            class Meta:
                model = Message
                fields = ('text', 'room')

        form_class = SendForm

        def get_form_kwargs(self):
            kwargs = super(MessageCRUDL.Send, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def form_valid(self, form):
            org = self.derive_org()
            room = form.cleaned_data['room']
            text = form.cleaned_data['text']
            msg = Message.create_for_user(org, self.request.user, text, room)
            return JsonResponse({'message_id': msg.pk})

    class List(OrgPermsMixin, SmartListView):
        paginate_by = None  # switch off Django pagination
        max_results = 10
        default_order = ('-id',)

        def get_queryset(self, **kwargs):
            org = self.derive_org()
            qs = Message.objects.filter(org=org)

            room_id = self.request.REQUEST.get('room', None)
            if room_id:
                qs = qs.filter(room_id=room_id)
            else:
                qs = qs.filter(room__in=self.request.user.get_all_rooms())

            if 'before_id' in self.request.REQUEST:
                qs = qs.filter(pk__lt=int(self.request.REQUEST['before_id']))

            if 'before_time' in self.request.REQUEST:
                qs = qs.filter(time__lt=parse_iso8601(self.request.REQUEST['before_time']))

            if 'after_id' in self.request.REQUEST:
                qs = qs.filter(pk__gt=int(self.request.REQUEST['after_id']))

            if 'after_time' in self.request.REQUEST:
                qs = qs.filter(time__gt=parse_iso8601(self.request.REQUEST['after_time']))

            return self.order_queryset(qs)

        def render_to_response(self, context, **response_kwargs):
            total = context['object_list'].count()
            messages = list(context['object_list'][:self.max_results])

            if messages:
                max_id = messages[0].pk
                min_id = messages[-1].pk
                has_older = len(messages) < total
            else:
                max_id = None
                min_id = None
                has_older = False

            results = [msg.as_json() for msg in messages]

            return JsonResponse({'count': len(results),
                                 'max_id': max_id,
                                 'min_id': min_id,
                                 'has_older': has_older,
                                 'results': results})


class HomeView(OrgPermsMixin, SmartTemplateView):
    """
    Chat homepage
    """
    title = _("Chat")
    template_name = 'chat/home.haml'
    permission = 'chat.room_user_home'

    def pre_process(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('users.user_login'))

        return super(HomeView, self).pre_process(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['rooms'] = self.request.user.get_all_rooms()
        return context
