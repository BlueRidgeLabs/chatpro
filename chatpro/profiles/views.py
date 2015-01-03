from __future__ import unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.validators import MinLengthValidator
from django.http import Http404
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
                                label=_("Chat name"), help_text=_("Name used for sending chat messages."))

    def __init__(self, *args, **kwargs):
        user = kwargs['user']
        del kwargs['user']
        self.user = user
        super(BaseProfileForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile


class UserForm(BaseProfileForm):
    """
    Form for user profiles
    """
    is_active = forms.BooleanField(label=_("Active"),
                                   help_text=_("Whether this user is active, disable to remove access."))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("Email address and login."))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New password"),
                                   help_text=_("Password used to log in (minimum of 8 characters, optional)."))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("Password used to log in (minimum of 8 characters)."))

    rooms = forms.ModelMultipleChoiceField(label=_("Rooms (chatting)"), queryset=Room.objects.filter(pk=-1),
                                           required=False,
                                           help_text=_("Chat rooms which this user can chat in."))

    manage_rooms = forms.ModelMultipleChoiceField(label=_("Rooms (manage)"), queryset=Room.objects.filter(pk=-1),
                                                  required=False,
                                                  help_text=_("Chat rooms which this user can manage."))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        if self.user.get_org():
            org_rooms = Room.objects.filter(org=self.user.get_org(), is_active=True).order_by('name')
            self.fields['rooms'].queryset = org_rooms
            self.fields['manage_rooms'].queryset = org_rooms


class ContactForm(BaseProfileForm):
    """
    Form for contact profiles
    """
    phone = forms.CharField(max_length=255, label=_("Phone"), help_text=_("Phone number of this contact."))

    room = forms.ModelChoiceField(label=_("Room"), queryset=Room.objects.filter(pk=-1),
                                  help_text=_("Chat rooms which this contact can chat in."))

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        if self.user.is_admin_for(self.user.get_org()):
            self.fields['room'].queryset = Room.objects.filter(org=self.user.get_org()).order_by('name')
        else:
            self.fields['room'].queryset = self.user.manage_rooms.all()


class ProfileCRUDL(SmartCRUDL):
    model = Profile
    actions = ('create_contact', 'list_contacts', 'update_contact',
               'create_user', 'list_users', 'update_user',
               'read', 'self')

    class CreateContact(OrgPermsMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'phone', 'room')
        form_class = ContactForm
        success_message = _("New contact created")
        success_url = '@profiles.profile_list_contacts'
        title = _("Create Contact")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.CreateContact, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def save(self, obj):
            org = self.request.user.get_org()
            urn = 'tel:%s' % self.form.cleaned_data['phone']
            room = self.form.cleaned_data['room']
            contact = Profile.create_contact(org, obj.full_name, obj.chat_name, urn, room, unicode(uuid4()))
            self.object = contact.profile

    class CreateUser(OrgPermsMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'rooms', 'manage_rooms')
        form_class = UserForm
        success_message = _("New user created")
        success_url = '@profiles.profile_list_users'
        title = _("Create User")

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

    class ListContacts(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'phone', 'room')
        title = _("Contacts")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/contacts/$' % path

        def get_queryset(self, **kwargs):
            qs = super(ProfileCRUDL.ListContacts, self).get_queryset(**kwargs)
            qs = qs.exclude(contact=None).select_related('contact')
            return qs

        def get_phone(self, obj):
            return obj.contact.get_urn()[1]

        def get_room(self, obj):
            return obj.contact.room

    class ListUsers(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'rooms', 'manage_rooms')
        title = _("Users")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/users/$' % path

        def get_queryset(self, **kwargs):
            qs = super(ProfileCRUDL.ListUsers, self).get_queryset(**kwargs)
            qs = qs.filter(user__in=self.request.org.get_org_editors()).select_related('user')
            return qs

        def get_email(self, obj):
            return obj.user.email

        def get_rooms(self, obj):
            return ", ".join([unicode(r) for r in obj.user.rooms.all()])

        def get_manage_rooms(self, obj):
            return ", ".join([unicode(r) for r in obj.user.manage_rooms.all()])

        def lookup_field_label(self, context, field, default=None):
            if field == 'manage_rooms':
                return _("Manages")
            else:
                return super(ProfileCRUDL.ListUsers, self).lookup_field_label(context, field, default)

    class UpdateContact(OrgPermsMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'phone', 'room')
        form_class = ContactForm
        success_message = _("Contact updated")
        title = _("Edit Contact")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.UpdateContact, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def derive_initial(self):
            initial = super(ProfileCRUDL.UpdateContact, self).derive_initial()
            initial['phone'] = self.object.contact.get_urn()[1]
            initial['room'] = self.object.contact.room
            return initial

        def post_save(self, obj):
            obj = super(ProfileCRUDL.UpdateContact, self).post_save(obj)
            obj.contact.urn = 'tel:%s' % self.form.cleaned_data['phone']
            obj.contact.room = self.form.cleaned_data['room']
            obj.contact.save()

    class UpdateUser(OrgPermsMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        form_class = UserForm
        success_message = _("User updated")
        title = _("Edit User")

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.UpdateUser, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def derive_initial(self):
            initial = super(ProfileCRUDL.UpdateUser, self).derive_initial()
            initial['email'] = self.object.user.email
            initial['rooms'] = self.object.user.rooms.all()
            initial['manage_rooms'] = self.object.user.manage_rooms.all()
            return initial

        def post_save(self, obj):
            obj = super(ProfileCRUDL.UpdateUser, self).post_save(obj)

            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.user.set_password(new_password)

            obj.user.email = self.form.cleaned_data['email']
            obj.user.is_active = self.form.cleaned_data['is_active']
            obj.user.save()

            obj.user.update_rooms(self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])
            return obj

    class Read(OrgPermsMixin, SmartReadView):
        fields = ('full_name', 'chat_name', 'type', 'rooms')

        def get_type(self, obj):
            if obj.is_contact():
                return _("Contact")
            elif obj.user.is_admin_for(self.request.org):
                return _("Administrator")
            else:
                return _("User")

        def get_rooms(self, obj):
            if obj.is_contact():
                return unicode(obj.contact.room)
            else:
                return ", ".join([unicode(r) for r in obj.user.rooms.all()])

    class Self(OrgPermsMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password')
        form_class = UserForm
        success_url = '@home.chat'
        success_message = _("Profile updated")
        title = _("Edit My Profile")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/self/$' % path

        def get_form_kwargs(self):
            kwargs = super(ProfileCRUDL.Self, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

        def get_object(self, queryset=None):
            queryset = Profile.objects.filter(user=self.request.user)
            try:
                return queryset.get()
            except queryset.model.DoesNotExist:
                raise Http404(_("User doesn't have a chat profile"))

        def has_permission(self, request, *args, **kwargs):
            return self.request.user.is_authenticated()

        def post_save(self, obj):
            obj = super(ProfileCRUDL.Self, self).post_save(obj)

            # update associated user
            obj.user.username = self.form.cleaned_data['email']
            obj.user.email = self.form.cleaned_data['email']

            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.user.set_password(new_password)

            obj.user.save()
            return obj
