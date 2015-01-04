from __future__ import unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartReadView, SmartUpdateView, SmartListView
from uuid import uuid4
from .models import Contact, Profile


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

    class Meta:
        model = User


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

    class Meta:
        model = Contact


class ProfileFormMixin(object):
    """
    Mixin for views that use a profile form
    """
    def get_form_kwargs(self):
        kwargs = super(ProfileFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def derive_initial(self):
        initial = super(ProfileFormMixin, self).derive_initial()
        if self.object:
            initial['full_name'] = self.object.profile.full_name
            initial['chat_name'] = self.object.profile.chat_name
        return initial

    def post_save(self, obj):
        obj = super(ProfileFormMixin, self).post_save(obj)
        obj.profile.full_name = self.form.cleaned_data['full_name']
        obj.profile.chat_name = self.form.cleaned_data['chat_name']
        obj.profile.save()
        return obj


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('create', 'update', 'list')

    class Create(OrgPermsMixin, ProfileFormMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'phone', 'room')
        form_class = ContactForm

        def save(self, obj):
            org = self.request.user.get_org()
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            urn = 'tel:%s' % self.form.cleaned_data['phone']
            self.object = Contact.create(org, full_name, chat_name, urn, obj.room, unicode(uuid4()))

    class Update(OrgPermsMixin, ProfileFormMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'phone', 'room')
        form_class = ContactForm

        def derive_initial(self):
            initial = super(ContactCRUDL.Update, self).derive_initial()
            initial['phone'] = self.object.get_urn()[1]
            return initial

        def pre_save(self, obj):
            obj = super(ContactCRUDL.Update, self).pre_save(obj)
            obj.urn = 'tel:%s' % self.form.cleaned_data['phone']
            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'phone', 'room')

        def get_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).get_queryset(**kwargs)
            qs = qs.filter(org=self.request.org, is_active=True).select_related('profile')
            return qs

        def get_full_name(self, obj):
            return obj.profile.full_name

        def get_chat_name(self, obj):
            return obj.profile.chat_name

        def get_phone(self, obj):
            return obj.get_urn()[1]


class UserCRUDL(SmartCRUDL):
    model = User
    actions = ('create', 'update', 'self', 'list')

    class Create(OrgPermsMixin, ProfileFormMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'rooms', 'manage_rooms')
        form_class = UserForm
        permission = 'profiles.profile_user_create'

        def save(self, obj):
            org = self.request.user.get_org()
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            rooms = self.form.cleaned_data['rooms']
            manage_rooms = self.form.cleaned_data['manage_rooms']
            self.object = Profile.create_user(org, full_name, chat_name, obj.email, password, rooms, manage_rooms)

    class Update(OrgPermsMixin, ProfileFormMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'rooms', 'manage_rooms', 'is_active')
        form_class = UserForm
        permission = 'profiles.profile_user_update'

        def pre_save(self, obj):
            obj.rooms.add(*self.form.cleaned_data['manage_rooms'])
            return obj

        def post_save(self, obj):
            obj = super(UserCRUDL.Update, self).post_save(obj)

            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)
                obj.save()

            return obj

    class Self(OrgPermsMixin, ProfileFormMixin, SmartUpdateView):
        """
        Limited update form for users to edit their own profiles
        """
        fields = ('full_name', 'chat_name', 'email', 'new_password')
        form_class = UserForm
        success_url = '@home.chat'
        success_message = _("Profile updated")
        title = _("Edit My Profile")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^profile/self/$'

        def has_permission(self, request, *args, **kwargs):
            return self.request.user.is_authenticated()

        def get_object(self, queryset=None):
            try:
                self.request.user.profile
            except Profile.DoesNotExist:
                raise Http404(_("User doesn't have a chat profile"))

            return self.request.user

        def post_save(self, obj):
            obj = super(UserCRUDL.Self, self).post_save(obj)

            new_password = self.form.cleaned_data.get('new_password', "")
            if new_password:
                obj.set_password(new_password)
                obj.save()
            return obj

    class List(OrgPermsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'rooms', 'manage_rooms')
        permission = 'profiles.profile_user_list'

        def get_queryset(self, **kwargs):
            qs = super(UserCRUDL.List, self).get_queryset(**kwargs)
            qs = qs.filter(pk__in=self.request.org.get_org_editors(), is_active=True).select_related('profile')
            return qs

        def get_full_name(self, obj):
            return obj.profile.full_name

        def get_chat_name(self, obj):
            return obj.profile.chat_name

        def get_rooms(self, obj):
            return ", ".join([unicode(r) for r in obj.rooms.all()])

        def get_manage_rooms(self, obj):
            return ", ".join([unicode(r) for r in obj.manage_rooms.all()])

        def lookup_field_label(self, context, field, default=None):
            if field == 'manage_rooms':
                return _("Manages")
            else:
                return super(UserCRUDL.List, self).lookup_field_label(context, field, default)


class ProfileCRUDL(SmartCRUDL):
    model = Profile
    actions = ('read',)

    class Read(OrgPermsMixin, SmartReadView):
        """
        Unified view of a contact or user
        """
        def derive_title(self):
            if self.object.is_user() and self.object.user == self.request.user:
                return _("My Profile")
            else:
                return super(ProfileCRUDL.Read, self).derive_title()

        def derive_fields(self):
            if self.object.is_contact():
                return 'full_name', 'chat_name', 'type', 'phone', 'room'
            elif self.object.user.is_admin_for(self.request.org):
                return 'full_name', 'chat_name', 'type', 'email'
            else:
                return 'full_name', 'chat_name', 'type', 'email', 'rooms'

        def get_type(self, obj):
            if obj.is_contact():
                return _("Contact")
            elif obj.user.is_admin_for(self.request.org):
                return _("Administrator")
            else:
                return _("User")

        def get_phone(self, obj):
            return obj.contact.get_urn()[1]

        def get_email(self, obj):
            return obj.user.email

        def get_room(self, obj):
            return unicode(obj.contact.room)

        def get_rooms(self, obj):
            return ", ".join([unicode(r) for r in obj.user.rooms.all()])
