from __future__ import unicode_literals

from chatpro.chat.models import Room
from dash.orgs.views import OrgPermsMixin
from dash.users.views import UserCRUDL as DashUserCRUDL
from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartUpdateView, SmartListView


class UserForm(forms.ModelForm):
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access"))

    full_name = forms.CharField(max_length=255,
                                label=_("Full name"))

    chat_name = forms.CharField(max_length=255,
                                label=_("Chat name"), help_text=_("Name used for sending chat messages"))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("Email address and login"))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New password"),
                                   help_text=_("Password used to log in (minimum of 8 characters, optional)"))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("Password used to log in (minimum of 8 characters)"))

    rooms = forms.ModelMultipleChoiceField(label=_("Rooms (chatting)"), queryset=Room.objects.filter(pk=-1),
                                           required=False,
                                           help_text=_("Chat rooms which this user can chat in"))

    manage_rooms = forms.ModelMultipleChoiceField(label=_("Rooms (manage)"), queryset=Room.objects.filter(pk=-1),
                                                  required=False,
                                                  help_text=_("Chat rooms which this user can manage"))

    def __init__(self, *args, **kwargs):
        org = kwargs['org']
        del kwargs['org']
        super(UserForm, self).__init__(*args, **kwargs)

        if org:
            org_rooms = Room.objects.filter(org=org, is_active=True).order_by('name')
            self.fields['rooms'].queryset = org_rooms
            self.fields['manage_rooms'].queryset = org_rooms

    class Meta:
        model = User


class UserFormViewMixin(object):
    form_class = UserForm

    def get_form_kwargs(self):
        kwargs = super(UserFormViewMixin, self).get_form_kwargs()
        kwargs['org'] = self.request.user.get_org()
        return kwargs

    def derive_initial(self):
        initial = super(UserFormViewMixin, self).derive_initial()
        if self.object:
            initial['full_name'] = self.object.profile.full_name
            initial['chat_name'] = self.object.profile.chat_name
        return initial


class AdministratorCRUDL(SmartCRUDL):
    model = User
    path = 'administrator'
    model_name = 'administrator'
    actions = ('create', 'update', 'list')

    class Create(OrgPermsMixin, UserFormViewMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password')
        success_message = _("New administrator created")
        success_url = '@users_ext.administrator_list'
        title = _("Create Administrator")

        def save(self, obj):
            org = self.request.user.get_org()
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            self.object = User.create_administrator(org, full_name, chat_name, obj.email, password)

    class Update(OrgPermsMixin, UserFormViewMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'is_active')
        success_url = '@users_ext.administrator_list'
        success_message = _("Administrator updated")
        title = _("Edit Administrator")

        def pre_save(self, obj):
            obj = super(AdministratorCRUDL.Update, self).pre_save(obj)
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)

            obj.profile.full_name = self.form.cleaned_data['full_name']
            obj.profile.chat_name = self.form.cleaned_data['chat_name']
            obj.profile.save()

            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email')
        title = _("Administrators")

        def get_queryset(self, **kwargs):
            qs = super(AdministratorCRUDL.List, self).get_queryset(**kwargs)
            org = self.request.user.get_org()
            if org:
                qs = qs.filter(pk__in=org.administrators.all())
            return qs

        def get_full_name(self, obj):
            return obj.profile.full_name

        def get_chat_name(self, obj):
            return obj.profile.chat_name


class UserCRUDL(SmartCRUDL):
    model = User
    actions = ('create', 'update', 'list', 'profile')

    class Create(OrgPermsMixin, UserFormViewMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'rooms', 'manage_rooms')
        success_url = '@users_ext.user_list'
        success_message = _("New user created")
        permission = 'chat.room_user_create'

        def save(self, obj):
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            self.object = User.create(self.request.user.get_org(), full_name, chat_name, obj.email, password,
                                      self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])

    class Update(OrgPermsMixin, UserFormViewMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        success_url = '@users_ext.user_list'
        success_message = _("User updated")
        permission = 'chat.room_user_update'

        def derive_initial(self):
            initial = super(UserCRUDL.Update, self).derive_initial()
            initial['rooms'] = self.object.rooms.all()
            initial['manage_rooms'] = self.object.manage_rooms.all()
            return initial

        def pre_save(self, obj):
            obj = super(UserCRUDL.Update, self).pre_save(obj)
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)

            obj.profile.full_name = self.form.cleaned_data['full_name']
            obj.profile.chat_name = self.form.cleaned_data['chat_name']
            obj.profile.save()

            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'rooms')
        permission = 'chat.room_user_list'

        def get_queryset(self, **kwargs):
            qs = super(UserCRUDL.List, self).get_queryset(**kwargs)
            org = self.request.user.get_org()
            qs = qs.filter(pk__in=org.editors.all())
            return qs

        def get_full_name(self, obj):
            return obj.get_full_name()

        def get_chat_name(self, obj):
            return obj.profile.chat_name

        def get_rooms(self, obj):
            return ", ".join([unicode(room) for room in obj.get_all_rooms()])

    class Profile(OrgPermsMixin, UserFormViewMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password')
        success_url = '@chat.home'
        success_message = _("Profile updated")
        title = _("Edit my profile")

        def has_permission(self, request, *args, **kwargs):
            return self.request.user.is_authenticated() and self.request.user.pk == int(kwargs['pk'])

        def pre_save(self, obj):
            obj = super(UserCRUDL.Profile, self).pre_save(obj)
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)

            obj.profile.full_name = self.form.cleaned_data['full_name']
            obj.profile.chat_name = self.form.cleaned_data['chat_name']
            obj.profile.save()

            return obj
