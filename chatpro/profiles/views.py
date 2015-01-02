from __future__ import unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartReadView, SmartUpdateView, SmartListView
from uuid import uuid4
from .models import Profile


class BaseProfileForm(forms.ModelForm):
    """
    Base form for profiles
    """
    full_name = forms.CharField(max_length=255,
                                label=_("Full name"))

    chat_name = forms.CharField(max_length=255,
                                label=_("Chat name"), help_text=_("Name used for sending chat messages"))

    def __init__(self, *args, **kwargs):
        user = kwargs['user']
        del kwargs['user']
        self.user = user
        super(BaseProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile


class AdminForm(BaseProfileForm):
    """
    Form for admin user profiles
    """
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access"))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("Email address and login"))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New password"),
                                   help_text=_("Password used to log in (minimum of 8 characters, optional)"))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("Password used to log in (minimum of 8 characters)"))


class UserForm(AdminForm):
    """
    Form for regular user profiles
    """
    rooms = forms.ModelMultipleChoiceField(label=_("Rooms (chatting)"), queryset=Room.objects.filter(pk=-1),
                                           required=False,
                                           help_text=_("Chat rooms which this user can chat in"))

    manage_rooms = forms.ModelMultipleChoiceField(label=_("Rooms (manage)"), queryset=Room.objects.filter(pk=-1),
                                                  required=False,
                                                  help_text=_("Chat rooms which this user can manage"))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        if self.user.get_org():
            org_rooms = Room.objects.filter(org=self.user.get_org(), is_active=True).order_by('name')
            self.fields['rooms'].queryset = org_rooms
            self.fields['manage_rooms'].queryset = org_rooms


class ContactForm(forms.ModelForm):
    """
    Form for contact profiles
    """
    phone = forms.CharField(max_length=255, label=_("Phone"), help_text=_("The phone number of the contact."))

    room = forms.ModelChoiceField(label=_("Room"), queryset=Room.objects.filter(pk=-1),
                                  required=False,
                                  help_text=_("The chat rooms which this user can chat in."))

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        if self.user.is_administrator():
            self.fields['room'].queryset = Room.objects.filter(org=self.user.get_org()).order_by('name')
        else:
            self.fields['room'].queryset = self.user.manage_rooms.all()


class ProfileCRUDL(SmartCRUDL):
    model = Profile
    actions = ('create_admin', 'create_user', 'create_contact',
               'list', 'admins',
               'read', 'update', 'profile')

    class CreateAdmin(OrgPermsMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password')
        form_class = AdminForm
        success_url = '@profiles.profile_list_admin'
        success_message = _("New admin created")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.CreateAdmin, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def save(self, obj):
            email = self.form.cleaned_data['email']
            password = self.form.cleaned_data['password']
            user = Profile.create_admin(self.request.user.get_org(), obj.full_name, obj.chat_name,
                                        email, password)
            self.object = user.profile

    class CreateUser(OrgPermsMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'rooms', 'manage_rooms')
        form_class = UserForm
        success_message = _("New user created")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.CreateUser, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def save(self, obj):
            email = self.form.cleaned_data['email']
            password = self.form.cleaned_data['password']
            user = Profile.create_user(self.request.user.get_org(), obj.full_name, obj.chat_name,
                                       email, password,
                                       self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])
            self.object = user.profile

    class CreateContact(OrgPermsMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'phone')
        form_class = ContactForm
        success_message = _("New contact created")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.CreateContact, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def save(self, obj):
            urn = 'tel:%s' % self.form.cleaned_data['phone']
            uuid = unicode(uuid4())
            contact = Profile.create_contact(self.request.user.get_org(), obj.full_name, obj.chat_name, urn,
                                             self.form.cleaned_data['room'], uuid)
            self.object = contact.profile

    class Read(OrgPermsMixin, SmartReadView):
        fields = ('full_name', 'chat_name', 'type', 'rooms')

        def get_type(self, obj):
            return _("Contact") if obj.is_contact() else _("User")

        def get_rooms(self, obj):
            if obj.is_contact():
                return unicode(obj.contact.room)
            else:
                return ", ".join([unicode(r) for r in obj.user.rooms.all()])

    class Update(OrgPermsMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        success_message = _("User updated")

        def get_form_class(self):
            if self.object.is_contact():
                return ContactForm
            elif self.object.user.is_administrator():
                return AdminForm
            else:
                return UserForm

        def derive_initial(self):
            initial = super(ProfileCRUDL.Update, self).derive_initial()
            initial['rooms'] = self.object.rooms.all()
            initial['manage_rooms'] = self.object.manage_rooms.all()
            return initial

        def pre_save(self, obj):
            obj = super(ProfileCRUDL.Update, self).pre_save(obj)
            obj.username = obj.email
            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)

            obj.profile.full_name = self.form.cleaned_data['full_name']
            obj.profile.chat_name = self.form.cleaned_data['chat_name']
            obj.profile.save()

            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'rooms')

        def get_queryset(self, **kwargs):
            qs = super(ProfileCRUDL.List, self).get_queryset(**kwargs)
            org = self.request.user.get_org()
            qs = qs.filter(user__pk__in=org.editors.all())
            return qs

        def get_rooms(self, obj):
            if obj.is_contact():
                return unicode(obj.contact.room)
            else:
                return ", ".join([unicode(r) for r in obj.user.rooms.all()])

    class Admins(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email')

        def get_queryset(self, **kwargs):
            qs = super(ProfileCRUDL.Admins, self).get_queryset(**kwargs)
            qs = qs.exclude(user=None)
            return qs

        def get_email(self, obj):
            return obj.user.email

    class Profile(OrgPermsMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password')
        success_url = '@chat.home'
        success_message = _("Profile updated")
        title = _("Edit my profile")

        def has_permission(self, request, *args, **kwargs):
            return self.request.user.is_authenticated() and self.request.user.pk == int(kwargs['pk'])

        def post_save(self, obj):
            obj = super(ProfileCRUDL.Profile, self).post_save(obj)

            # update associated user
            obj.user.username = self.form.cleaned_data['email']
            obj.user.email = self.form.cleaned_data['email']

            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.user.set_password(new_password)

            obj.user.save()
            return obj
