from __future__ import unicode_literals

from chatpro.chat.models import Room
from dash.orgs.views import OrgPermsMixin
from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartUpdateView, SmartListView


class UserForm(forms.ModelForm):
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access"))

    full_name = forms.CharField(max_length=255,
                                label=_("Full Name"), help_text=_("The full name of the user"))

    chat_name = forms.CharField(max_length=255,
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

        org_rooms = Room.objects.filter(org=org, is_active=True).order_by('name')
        self.fields['rooms'].queryset = org_rooms
        self.fields['manage_rooms'].queryset = org_rooms

    class Meta:
        model = User


class UserCRUDL(SmartCRUDL):
    model = User
    actions = ('create', 'update', 'list')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = UserForm
        fields = ('full_name', 'chat_name', 'email', 'password', 'rooms', 'manage_rooms')
        success_url = '@users_ext.user_list'
        success_message = _("New user created")
        permission = 'chat.room_user_create'

        def get_form_kwargs(self):
            kwargs = super(UserCRUDL.Create, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def save(self, obj):
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            self.object = User.create(self.request.user.get_org(), full_name, chat_name, obj.email, password,
                                      self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])

    class Update(OrgPermsMixin, SmartUpdateView):
        form_class = UserForm
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        success_url = '@users_ext.user_list'
        success_message = _("User updated")
        permission = 'chat.room_user_update'

        def get_form_kwargs(self):
            kwargs = super(UserCRUDL.Update, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def derive_initial(self):
            initial = super(UserCRUDL.Update, self).derive_initial()
            initial['full_name'] = self.object.full_name
            initial['chat_name'] = self.object.chat_name
            initial['rooms'] = self.object.rooms.all()
            initial['manage_rooms'] = self.object.manage_rooms.all()
            return initial

        def lookup_field_label(self, context, field, default=None):
            if field == 'email':
                return _('Email / Login')

            return super(UserCRUDL.Update, self).lookup_field_label(context, field, default)

        def pre_save(self, obj):
            obj = super(UserCRUDL.Update, self).pre_save(obj)
            obj.first_name = self.form.cleaned_data['full_name']
            obj.last_name = self.form.cleaned_data['chat_name']
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)
            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'rooms')
        permission = 'chat.room_user_list'

        def get_queryset(self, **kwargs):
            qs = super(UserCRUDL.List, self).get_queryset(**kwargs)
            org = self.request.user.get_org()
            qs = qs.filter(pk__in=org.editors.all())
            return qs

        def get_rooms(self, obj):
            return ", ".join([unicode(room) for room in obj.get_all_rooms()])
