# -*- coding: utf-8 -*-

import datetime
import warnings

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.timezone import utc
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.utils.datastructures import SortedDict

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit

from core.models import Setting


class BaseProfileForm(forms.Form):
    required_css_class = 'required'

    first_name = forms.CharField(label=_(u'Имя'))
    last_name = forms.CharField(label=_(u'Фамилия'))

    def clean_first_name(self):
        return self.cleaned_data['first_name'].title()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].title()


class EditForm(BaseProfileForm):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'edit-profile-form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset('', 'first_name', 'last_name'),
            Submit('submit', _('Save Changes')),
        )
        super(EditForm, self).__init__(*args, **kwargs)


class BasePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label=_(u'Пароль'))
    password_confirm = forms.CharField(widget=forms.PasswordInput, label=_(u'Пароль ещё раз'))

    def clean(self):
        if 'password' in self.cleaned_data and 'password_confirm' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password_confirm']:
                raise forms.ValidationError(_(u'Пароли не совпадают.'))

        return self.cleaned_data


from django.core import validators
from apps.users.models import UserSignup
class SignupForm(BaseProfileForm, BasePasswordForm):
    email = forms.CharField(label=_(u'E-mail'), help_text=u'E-mail', validators=[validators.EmailValidator(message=u'Введите корректный E-mail адрес.')])

    def clean_email(self):
        user = get_user_model().objects.filter(email=self.cleaned_data['email'])
        if user.exists():
            if user[0].is_active:
                raise forms.ValidationError(_(u'Указанный Вами e-mail уже используется'))
            else:
                user_signup = UserSignup.objects.get(user__email=self.cleaned_data['email'])
                user_signup_utc = user_signup.created
                current_utc = datetime.datetime.utcnow().replace(tzinfo=utc)
                if current_utc - user_signup_utc < datetime.timedelta(hours=24):
                    time_remaining = str(datetime.timedelta(hours=24) - (current_utc - user_signup_utc))[:-7]
                    raise forms.ValidationError(u'Попробуйте через ' + time_remaining)
                else:
                    user_signup.user.delete()
                    user_signup.delete()

        return self.cleaned_data['email']

    def __init__(self, *args, **kwargs):
        """Упорядычиваем поля"""
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['first_name', 'last_name', 'email', 'password', 'password_confirm']


class LoginForm(forms.Form):
    username = forms.CharField(max_length=254, label=_(u'E-mail'))
    password = forms.CharField(label=_(u'Пароль'), widget=forms.PasswordInput)

    error_messages = {
        'invalid_login': _(u'Пожалуйста, введите коррекный e-mail и пароль.'),
        'inactive': _(u'Аккаунт не активен.'),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

        # Set the label for the "username" field.
        UserModel = get_user_model()
        self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
        return self.cleaned_data

    def check_for_test_cookie(self):
        warnings.warn("check_for_test_cookie is deprecated; ensure your login view is CSRF-protected.", DeprecationWarning)

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_(u"E-mail"), max_length=254)

    def clean_email(self):
        user = get_user_model().objects.filter(email=self.cleaned_data['email'])
        if not user.exists():
            raise forms.ValidationError(_(u'Пользователя с указанным e-mail не существует.'))
        return self.cleaned_data['email']

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from django.core.mail import send_mail
        UserModel = get_user_model()
        email = self.cleaned_data["email"]
        active_users = UserModel._default_manager.filter(
            email__iexact=email, is_active=True)
        for user in active_users:
            # Make sure that no email is sent to a user that actually has
            # a password marked as unusable
            if not user.has_usable_password():
                continue
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            site = Setting.objects.all()[0] if Setting.objects.count() > 0 else None
            c = {
                'email': user.email,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'site': site,
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])


class EditEmailForm(forms.Form):
    email = forms.EmailField(label=_(u'E-mail'))

    def clean_email(self):
        user = get_user_model().objects.filter(email=self.cleaned_data['email'])
        if user.exists():
            if user[0].is_active:
                raise forms.ValidationError(_(u'Указанный Вами e-mail уже используется'))
            else:
                user_signup = UserSignup.objects.get(user__email=self.cleaned_data['email'])
                user_signup_utc = user_signup.created
                current_utc = datetime.datetime.utcnow().replace(tzinfo=utc)
                if current_utc - user_signup_utc < datetime.timedelta(hours=24):
                    time_remaining = str(datetime.timedelta(hours=24) - (current_utc - user_signup_utc))[:-7]
                    raise forms.ValidationError(u'Попробуйте через ' + time_remaining)

        return self.cleaned_data['email']


class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set his/her password without entering the
    old password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class PasswordChangeForm(SetPasswordForm):
    """
    A form that lets a user change his/her password by entering
    their old password.
    """
    error_messages = dict(SetPasswordForm.error_messages, **{
        'password_incorrect': _(u"Старый пароль введён не верно."),
    })
    old_password = forms.CharField(label=_("Old password"),
                                   widget=forms.PasswordInput)

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

PasswordChangeForm.base_fields = SortedDict([
    (k, PasswordChangeForm.base_fields[k])
    for k in ['old_password', 'new_password1', 'new_password2']
])