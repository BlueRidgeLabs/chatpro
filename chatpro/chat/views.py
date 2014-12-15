from __future__ import unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.validators import MinLengthValidator
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCreateView, SmartFormView, SmartListView, SmartTemplateView, SmartUpdateView
from smartmin.users.views import SmartCRUDL
from .models import Contact, Room, User


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
    actions = ('create', 'update', 'list')

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

        def get_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).get_queryset(**kwargs)

            org = self.request.user.get_org()
            qs = qs.filter(org=org, is_active=True).order_by('name')

            rooms = self.request.user.get_all_rooms()
            if rooms is not None:
                qs = qs.filter(room__in=rooms)
            return qs

        def get_phone(self, obj):
            return obj.get_urn()[1]


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


class UserForm(forms.ModelForm):
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access"))

    name = forms.CharField(max_length=255,
                           label=_("Name"), help_text=_("The full name of the user"))

    chatname = forms.CharField(max_length=255,
                               label=_("Chat Name"), help_text=_("The chat name of the user"))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("The email address and login for the user"))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New Password"),
                                   help_text=_("The password used to log in (minimum of 8 characters, optional)"))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("The password used to log in (minimum of 8 characters)"))

    rooms = forms.ModelMultipleChoiceField(label=_("Rooms (Chat)"), queryset=Room.objects.filter(pk=-1),
                                           required=False,
                                           help_text=_("The chat rooms which this user can chat in."))

    manage_rooms = forms.ModelMultipleChoiceField(label=_("Rooms (Manage)"), queryset=Room.objects.filter(pk=-1),
                                                  required=False,
                                                  help_text=_("The chat rooms which this user can manage."))

    def __init__(self, *args, **kwargs):
        org = kwargs['org']
        del kwargs['org']
        super(UserForm, self).__init__(*args, **kwargs)

        org_rooms = Room.objects.filter(org=org).order_by('name')
        self.fields['rooms'].queryset = org_rooms
        self.fields['manage_rooms'].queryset = org_rooms

    class Meta:
        model = User


class UserCRUDL(SmartCRUDL):
    model = User
    actions = ('create', 'update', 'list', 'chat')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = UserForm
        fields = ('name', 'chatname', 'email', 'password', 'rooms', 'manage_rooms')
        success_url = '@chat.user_list'
        success_message = _("New user created")

        def get_form_kwargs(self):
            kwargs = super(UserCRUDL.Create, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def save(self, obj):
            name = self.form.cleaned_data['name']  # obj field is actually first_name
            password = self.form.cleaned_data['password']
            self.object = User.create(self.request.user.get_org(), name, obj.chatname, obj.email, password,
                                      self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])

    class Update(OrgPermsMixin, SmartUpdateView):
        form_class = UserForm
        fields = ('name', 'chatname', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        success_url = '@chat.user_list'
        success_message = _("User updated")

        def get_form_kwargs(self):
            kwargs = super(UserCRUDL.Update, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def derive_initial(self):
            initial = super(UserCRUDL.Update, self).derive_initial()
            initial['name'] = self.object.first_name
            initial['rooms'] = self.object.rooms.all()
            initial['manage_rooms'] = self.object.manage_rooms.all()
            return initial

        def pre_save(self, obj):
            obj = super(UserCRUDL.Update, self).pre_save(obj)
            obj.first_name = self.form.cleaned_data['name']
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)
            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'email', 'chatname', 'rooms')

        def derive_queryset(self, **kwargs):
            return super(UserCRUDL.List, self).derive_queryset(**kwargs).filter(org=self.request.user.get_org())

        def get_rooms(self, obj):
            return ", ".join([unicode(room) for room in obj.get_all_rooms()])

    class Chat(OrgPermsMixin, SmartTemplateView):
        title = _("Chat")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^home/$'

        def get_context_data(self, **kwargs):
            context = super(UserCRUDL.Chat, self).get_context_data(**kwargs)
            context['rooms'] = self.request.user.get_all_rooms()
            return context
