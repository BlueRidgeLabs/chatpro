from __future__ import unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.validators import MinLengthValidator
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartFormView, SmartListView, SmartUpdateView
from .models import Contact, Room, Supervisor


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('list',)

    class List(OrgPermsMixin, SmartListView):
        def derive_fields(self):
            rooms = self.request.user.get_rooms()
            if rooms is not None:
                return 'name', 'urn'
            else:
                return 'room', 'name', 'urn'

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()

            qs = super(ContactCRUDL.List, self).get_queryset(**kwargs)
            qs = qs.filter(org=org)

            rooms = self.request.user.get_rooms()
            if rooms is not None:
                qs = qs.filter(room__in=rooms)
            return qs


class RoomCRUDL(SmartCRUDL):
    model = Room
    actions = ('list', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name',)

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()

            qs = super(RoomCRUDL.List, self).get_queryset(**kwargs)
            return qs.filter(org=org)

    class Select(OrgPermsMixin, SmartFormView):
        class GroupsForm(forms.Form):
            groups = forms.MultipleChoiceField(choices=(), label=_("Groups"),
                                               help_text=_("Contact groups to be used as chat rooms"))

            def __init__(self, *args, **kwargs):
                self.org = kwargs['org']
                del kwargs['org']
                super(RoomCRUDL.Select.GroupsForm, self).__init__(*args, **kwargs)

                choices = []
                for group in self.org.get_temba_client().get_groups():
                    choices.append((group['group'], "%s (%d)" % (group['name'], group['size'])))

                self.fields['groups'].choices = choices

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
            groups = form.cleaned_data['groups']

            # TODO implement syncing rooms with groups etc
            print "USER SELECTED: %s" % str(groups)

            return HttpResponseRedirect(self.get_success_url())


class SupervisorForm(forms.Form):
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access"))

    name = forms.CharField(max_length=255,
                           label=_("Name"), help_text=_("The name of the user"))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("The email address for the user"))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New Password"),
                                   help_text=_("The password used to log in (minimum of 8 characters, optional)"))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("The password used to log in (minimum of 8 characters)"))

    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.filter(pk=-1),
                                           label=_("Rooms"), help_text=_("The chat rooms which this user can supervise"))

    def __init__(self, *args, **kwargs):
        self.org = kwargs['org']
        del kwargs['org']
        super(SupervisorForm, self).__init__(*args, **kwargs)

        self.fields['rooms'].queryset = Room.objects.filter(org=self.org).order_by('name')


class SupervisorCRUDL(SmartCRUDL):
    model = Supervisor
    actions = ('create', 'list', 'update')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'username', 'rooms')

        def derive_queryset(self, **kwargs):
            return super(SupervisorCRUDL.List, self).derive_queryset(**kwargs).filter(org=self.request.user.get_org())

        def get_rooms(self, obj):
            return ", ".join([unicode(room) for room in obj.get_rooms()])

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = SupervisorForm
        fields = ('name', 'email', 'password', 'rooms')

        def get_form_kwargs(self):
            kwargs = super(SupervisorCRUDL.Create, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def save(self, obj):
            org = self.request.user.get_org()
            name = self.form.cleaned_data['name']
            email = self.form.cleaned_data['email']
            password = self.form.cleaned_data['password']
            rooms = self.form.cleaned_data['rooms']
            self.object = Supervisor.create(org, name, email, password, rooms)

    class Update(OrgPermsMixin, SmartUpdateView):
        form_class = SupervisorForm
        fields = ('is_active', 'name', 'email', 'new_password', 'rooms')

        def derive_initial(self):
            initial = super(SupervisorCRUDL.Update, self).derive_initial()
            initial['rooms'] = self.object.get_rooms()
            return initial

        def pre_save(self, obj):
            obj = super(SupervisorCRUDL.Update, self).pre_save(obj)
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)
            return obj
