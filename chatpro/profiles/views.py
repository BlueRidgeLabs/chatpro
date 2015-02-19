from __future__ import absolute_import, unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import get_obj_cacheable
from dash.utils.sync import ChangeType
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.validators import MinLengthValidator
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartCreateView, SmartReadView, SmartUpdateView, SmartListView, SmartDeleteView
from .models import Contact


URN_SCHEME_TEL = 'tel'
URN_SCHEME_TWITTER = 'twitter'
URN_SCHEME_CHOICES = ((URN_SCHEME_TEL, _("Phone")), (URN_SCHEME_TWITTER, _("Twitter")))


class URNField(forms.fields.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (forms.ChoiceField(choices=URN_SCHEME_CHOICES),
                  forms.CharField(max_length=32))
        super(URNField, self).__init__(fields, *args, **kwargs)

        self.widget = URNWidget(scheme_choices=URN_SCHEME_CHOICES)

    def compress(self, values):
        return '%s:%s' % (values[0], values[1])


class URNWidget(forms.widgets.MultiWidget):
    def __init__(self, *args, **kwargs):
        scheme_choices = kwargs.pop('scheme_choices')

        widgets = (forms.Select(choices=scheme_choices),
                   forms.TextInput(attrs={'maxlength': 32}))
        super(URNWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split(':', 1)
        else:
            return URN_SCHEME_TEL, ''

    def render(self, name, value, attrs=None):
        output = ['<div class="urn-widget">',
                  super(URNWidget, self).render(name, value, attrs),
                  '</div>']
        return mark_safe(''.join(output))


class AbstractParticipantForm(forms.ModelForm):
    """
    Base form for chat participants
    """
    full_name = forms.CharField(max_length=128,
                                label=_("Full name"))

    chat_name = forms.CharField(max_length=16,
                                label=_("Chat name"), help_text=_("Name used for sending chat messages."))

    def __init__(self, *args, **kwargs):
        self.user = kwargs['user']
        del kwargs['user']
        super(AbstractParticipantForm, self).__init__(*args, **kwargs)


class ContactForm(AbstractParticipantForm):
    """
    Form for contact profiles
    """
    urn = URNField(label=_("Phone/Twitter"), help_text=_("Phone number or Twitter handle of this contact."))

    room = forms.ModelChoiceField(label=_("Room"), queryset=Room.objects.filter(pk=-1),
                                  help_text=_("Chat room which this contact can chat in."))

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        if self.user.is_admin_for(self.user.get_org()):
            self.fields['room'].queryset = Room.get_all(self.user.get_org()).order_by('name')
        else:
            self.fields['room'].queryset = self.user.manage_rooms.all()

    class Meta:
        model = Contact
        exclude = ()


class ParticipantFormMixin(object):
    """
    Mixin for views that use a participant form
    """
    def get_form_kwargs(self):
        kwargs = super(ParticipantFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ContactFieldsMixin(object):
    def get_urn(self, obj):
        # TODO indicate different urn types with icon?
        return obj.get_urn()[1]

    def lookup_field_label(self, context, field, default=None):
        if field == 'urn':
            return _("Phone/Twitter")

        return super(ContactFieldsMixin, self).lookup_field_label(context, field, default)


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('create', 'update', 'read', 'list', 'filter', 'delete')

    class Create(OrgPermsMixin, ParticipantFormMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'urn', 'room')
        form_class = ContactForm

        def dispatch(self, request, *args, **kwargs):
            return super(ContactCRUDL.Create, self).dispatch(request, *args, **kwargs)

        def derive_initial(self):
            initial = super(ContactCRUDL.Create, self).derive_initial()
            room_id = self.kwargs.get('room', None)
            if room_id:
                initial['room'] = Room.objects.get(org=self.request.org, pk=room_id)
            return initial

        def save(self, obj):
            org = self.request.user.get_org()
            self.object = Contact.create(org, self.request.user, obj.full_name, obj.chat_name, obj.urn, obj.room)

    class Update(OrgObjPermsMixin, ParticipantFormMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'urn', 'room')
        form_class = ContactForm

        def dispatch(self, request, *args, **kwargs):
            return super(ContactCRUDL.Update, self).dispatch(request, *args, **kwargs)

        def post_save(self, obj):
            obj = super(ContactCRUDL.Update, self).post_save(obj)
            obj.push(ChangeType.updated)
            return obj

    class Read(OrgPermsMixin, SmartReadView):
        def derive_fields(self):
            fields = ['full_name', 'chat_name', 'type', 'urn', 'room']
            if self.object.created_by_id:
                fields += ['added_by']
            return fields

        def get_queryset(self):
            queryset = super(ContactCRUDL.Read, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True)

        def get_context_data(self, **kwargs):
            context = super(ContactCRUDL.Read, self).get_context_data(**kwargs)
            edit_button_url = None
            delete_button_url = None

            room = self.object.room
            if self.request.user.has_room_access(room, manage=True):
                if self.has_org_perm('profiles.contact_update'):
                    edit_button_url = reverse('profiles.contact_update', args=[self.object.pk])
                if self.has_org_perm('profiles.contact_delete'):
                    delete_button_url = reverse('profiles.contact_delete', args=[self.object.pk])

            context['edit_button_url'] = edit_button_url
            context['delete_button_url'] = delete_button_url
            return context

        def get_type(self, obj):
            return _("Contact")

        def get_urn(self, obj):
            return obj.get_urn()[1]

        def get_added_by(self, obj):
            return obj.created_by.get_full_name()

        def lookup_field_label(self, context, field, default=None):
            if field == 'urn':
                scheme = self.object.get_urn()[0]
                for s, label in URN_SCHEME_CHOICES:
                    if scheme == s:
                        return label

            return super(ContactCRUDL.Read, self).lookup_field_label(context, field, default)

    class List(OrgPermsMixin, ContactFieldsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'urn', 'room')
        default_order = ('full_name',)

        def derive_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).derive_queryset(**kwargs)

            rooms = self.request.user.get_rooms(self.request.org)
            return qs.filter(org=self.request.org, is_active=True, room__in=rooms)

    class Filter(OrgPermsMixin, ContactFieldsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'urn')
        default_order = ('full_name',)

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<room>\d+)/$' % (path, action)

        def derive_title(self):
            return _("Contacts in %s") % self.derive_room().name

        def derive_room(self):
            def fetch():
                room = Room.objects.filter(pk=self.kwargs['room'], org=self.request.org).first()
                if not room:
                    raise Http404("No such room in this org")

                if room not in self.request.user.get_rooms(self.request.org):
                    raise PermissionDenied()
                return room

            return get_obj_cacheable(self, '_room', fetch)

        def derive_queryset(self, **kwargs):
            return self.derive_room().get_contacts()

        def get_context_data(self, **kwargs):
            context = super(ContactCRUDL.Filter, self).get_context_data(**kwargs)
            context['room'] = self.derive_room()
            return context

    class Delete(OrgObjPermsMixin, SmartDeleteView):
        cancel_url = '@profiles.contact_list'

        def post(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.request.user.has_room_access(self.object.room, manage=True):
                self.pre_delete(self.object)
                self.object.release()
                return HttpResponseRedirect(reverse('profiles.contact_list'))
            else:
                raise PermissionDenied()


class UserForm(AbstractParticipantForm):
    """
    Form for user profiles
    """
    is_active = forms.BooleanField(label=_("Active"), required=False,
                                   help_text=_("Whether this user is active, disable to remove access."))

    email = forms.CharField(max_length=256,
                            label=_("Email"), help_text=_("Email address and login."))

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)],
                               label=_("Password"), help_text=_("Password used to log in (minimum of 8 characters)."))

    new_password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8)], required=False,
                                   label=_("New password"),
                                   help_text=_("Password used to login (minimum of 8 characters, optional)."))

    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label=_("Confirm password"))

    change_password = forms.BooleanField(label=_("Require change"), required=False,
                                         help_text=_("Whether user must change password on next login."))

    rooms = forms.ModelMultipleChoiceField(label=_("Rooms (chatting)"), queryset=Room.objects.all(),
                                           required=False,
                                           help_text=_("Chat rooms which this user can chat in."))

    manage_rooms = forms.ModelMultipleChoiceField(label=_("Rooms (manage)"), queryset=Room.objects.all(),
                                                  required=False,
                                                  help_text=_("Chat rooms which this user can manage."))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        if self.user.get_org():
            org_rooms = Room.get_all(self.user.get_org()).order_by('name')
            self.fields['rooms'].queryset = org_rooms
            self.fields['manage_rooms'].queryset = org_rooms

    def clean(self):
        cleaned_data = super(UserForm, self).clean()

        password = cleaned_data.get('password', None) or cleaned_data.get('new_password', None)
        if password:
            confirm_password = cleaned_data.get('confirm_password', '')
            if password != confirm_password:
                self.add_error('confirm_password', _("Passwords don't match."))

    class Meta:
        model = User
        exclude = ()


class UserFormMixin(ParticipantFormMixin):
    """
    Mixin for views that use a user form
    """
    def derive_initial(self):
        initial = super(UserFormMixin, self).derive_initial()
        if self.object:
            initial['full_name'] = self.object.profile.full_name
            initial['chat_name'] = self.object.profile.chat_name
        return initial

    def post_save(self, obj):
        obj = super(UserFormMixin, self).post_save(obj)
        data = self.form.cleaned_data
        obj.profile.full_name = data['full_name']
        obj.profile.chat_name = data['chat_name']
        obj.profile.save()

        password = data.get('new_password', None) or data.get('password', None)
        if password:
            obj.set_password(password)
            obj.save()

        return obj


class UserFieldsMixin(object):
    def get_full_name(self, obj):
        return obj.profile.full_name

    def get_chat_name(self, obj):
        return obj.profile.chat_name

    def get_rooms(self, obj):
        return ", ".join([unicode(r) for r in obj.rooms.all()])


class UserCRUDL(SmartCRUDL):
    model = User
    actions = ('create', 'update', 'read', 'self', 'list')

    class Create(OrgPermsMixin, UserFormMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'confirm_password', 'change_password', 'rooms', 'manage_rooms')
        form_class = UserForm
        permission = 'profiles.profile_user_create'
        success_message = _("New supervisor created")
        title = _("Create Supervisor")

        def save(self, obj):
            org = self.request.user.get_org()
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            change_password = self.form.cleaned_data['change_password']
            rooms = self.form.cleaned_data['rooms']
            manage_rooms = self.form.cleaned_data['manage_rooms']
            self.object = User.create(org, full_name, chat_name, obj.email,
                                      password, change_password,
                                      rooms, manage_rooms)

    class Update(OrgPermsMixin, UserFormMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'confirm_password', 'rooms', 'manage_rooms', 'is_active')
        form_class = UserForm
        permission = 'profiles.profile_user_update'
        success_message = _("Supervisor updated")
        title = _("Edit Supervisor")

        def derive_initial(self):
            initial = super(UserCRUDL.Update, self).derive_initial()
            initial['rooms'] = self.object.rooms.all()
            initial['manage_rooms'] = self.object.manage_rooms.all()
            return initial

        def post_save(self, obj):
            obj = super(UserCRUDL.Update, self).post_save(obj)
            obj.update_rooms(self.form.cleaned_data['rooms'], self.form.cleaned_data['manage_rooms'])
            return obj

    class Self(OrgPermsMixin, UserFormMixin, SmartUpdateView):
        """
        Limited update form for users to edit their own profiles
        """
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
            if not self.request.user.has_profile():
                raise Http404(_("User doesn't have a chat profile"))

            return self.request.user

        def pre_save(self, obj):
            obj = super(UserCRUDL.Self, self).pre_save(obj)
            if 'password' in self.form.cleaned_data:
                self.object.profile.change_password = False

            return obj

        def derive_fields(self):
            fields = ['full_name', 'chat_name', 'email']
            if self.object.profile.change_password:
                fields += ['password']
            else:
                fields += ['new_password']
            return fields + ['confirm_password']

    class Read(OrgPermsMixin, UserFieldsMixin, SmartReadView):
        permission = 'profiles.profile_user_read'

        def derive_title(self):
            if self.object == self.request.user:
                return _("My Profile")
            else:
                return super(UserCRUDL.Read, self).derive_title()

        def derive_fields(self):
            fields = ['full_name', 'chat_name', 'type', 'email']
            if not self.object.is_admin_for(self.request.org):
                fields += ['rooms']
            return fields

        def get_queryset(self):
            qs = super(UserCRUDL.Read, self).get_queryset()

            # only allow access to active editors or administrators attached to this org
            org = self.request.org
            qs = qs.filter(Q(org_editors=org) | Q(org_admins=org)).filter(is_active=True)
            return qs.select_related('profile').distinct()

        def get_context_data(self, **kwargs):
            context = super(UserCRUDL.Read, self).get_context_data(**kwargs)
            edit_button_url = None

            if self.object == self.request.user:
                edit_button_url = reverse('profiles.user_self')
            elif self.has_org_perm('profiles.profile_user_update'):
                edit_button_url = reverse('profiles.user_update', args=[self.object.pk])

            context['edit_button_url'] = edit_button_url
            return context

        def get_type(self, obj):
            if obj.is_admin_for(self.request.org):
                return _("Administrator")
            else:
                return _("Supervisor")

    class List(OrgPermsMixin, UserFieldsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'rooms', 'manages')
        default_order = ('profile__full_name',)
        permission = 'profiles.profile_user_list'
        title = _("Supervisors")

        def derive_queryset(self, **kwargs):
            qs = super(UserCRUDL.List, self).derive_queryset(**kwargs)

            # only show active editors - exclude administrators
            org = self.request.org
            qs = qs.filter(org_editors=org, is_active=True).exclude(org_admins=org)
            return qs.select_related('profile').distinct()

        def get_manages(self, obj):
            return ", ".join([unicode(r) for r in obj.manage_rooms.all()])


class ManageUserCRUDL(SmartCRUDL):
    """
    CRUDL used only by superusers to manage users outside the context of an organization
    """
    model = User
    model_name = 'Admin'
    path = 'admin'
    actions = ('create', 'update', 'list')

    class Create(OrgPermsMixin, UserFormMixin, SmartCreateView):
        fields = ('full_name', 'chat_name', 'email', 'password', 'confirm_password', 'change_password')
        form_class = UserForm

        def save(self, obj):
            full_name = self.form.cleaned_data['full_name']
            chat_name = self.form.cleaned_data['chat_name']
            password = self.form.cleaned_data['password']
            change_password = self.form.cleaned_data['change_password']
            self.object = User.create(None, full_name, chat_name, obj.email, password, change_password)

    class Update(OrgPermsMixin, UserFormMixin, SmartUpdateView):
        fields = ('full_name', 'chat_name', 'email', 'new_password', 'confirm_password', 'is_active')
        form_class = UserForm

    class List(UserFieldsMixin, SmartListView):
        fields = ('full_name', 'chat_name', 'email', 'orgs')
        default_order = ('profile__full_name',)

        def derive_queryset(self, **kwargs):
            qs = super(ManageUserCRUDL.List, self).derive_queryset(**kwargs)
            return qs.filter(is_active=True).exclude(profile=None).select_related('profile', 'org_admins', 'org_editors')

        def get_orgs(self, obj):
            orgs = set(obj.org_admins.all()) | set(obj.org_editors.all())
            return ", ".join([unicode(o) for o in orgs])

        def lookup_field_link(self, context, field, obj):
            return reverse('profiles.admin_update', args=[obj.pk])
