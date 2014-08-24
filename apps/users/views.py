# -*- coding: utf-8 -*-

import datetime

from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.models import get_current_site
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode
from django.shortcuts import resolve_url
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.timezone import utc

from apps.users.forms import EditForm, SignupForm, LoginForm, PasswordResetForm, EditEmailForm, PasswordChangeForm, SetPasswordForm
from apps.users.models import UserSignup, User


def user(request, user_id):

    if int(user_id) == int(request.user.id) and request.user.is_authenticated() and not request.user.is_active:
        messages.add_message(request, messages.INFO, u'Пожалуйста, подтвердите, что <b>{0}</b> - действительно Ваш E-mail адрес. <a href="{1}">Выслать повторное письмо для подтверждения</a>'.format(request.user.email, reverse('send_activate')), extra_tags='safe')

    return render(request, 'users/profile.html', {
        'profile': get_object_or_404(get_user_model(), id=user_id)
    })


@login_required
def edit_email(request):
    form = EditEmailForm(request.POST or None)
    if form.is_valid():
        for u in User.objects.filter(email=form.cleaned_data['email']):
            u.signup.delete()
            u.delete()
        request.user.email = form.cleaned_data['email']
        request.user.is_active = False
        request.user.save()
        UserSignup.objects.activate_email(request.user)
        messages.add_message(request, messages.INFO, u'Мы отправили Вам письмо на <b>{0}</b> для подтверждения активации.'.format(form.cleaned_data['email']), extra_tags='safe')
        form = EditEmailForm()

    return render(request, 'users/edit_email.html', {'form': form})


@login_required
def send_activate(request):

    user = get_user_model().objects.filter(email=request.user.email)
    if user.exists() and user[0].id != request.user.id:
        messages.add_message(request, messages.ERROR, u'E-mail адрес {0} уже кто-то занял.'.format(request.user.signup.email))
        return redirect(reverse('edit_email'))

    if request.user.is_active:
        if not request.user.signup:
            messages.add_message(request, messages.INFO, u'Ваш E-mail уже подтверждён.', extra_tags='safe')
        else:
            UserSignup.objects.activate_email(request.user)
            messages.add_message(request, messages.INFO, u'Мы отправили Вам письмо на <b>{0}</b> для подтверждения активации.'.format(request.user.signup.email), extra_tags='safe')
        return redirect(reverse('edit_email'))

    else:
        UserSignup.objects.activate_email(request.user)
        messages.add_message(request, messages.INFO, u'Мы отправили Вам письмо на <b>{0}</b> для подтверждения активации.'.format(request.user.email), extra_tags='safe')


    return redirect(reverse('user', args=(request.user.id,)))


class EditFormView(FormView):
    form_class = EditForm
    template_name = 'users/edit.html'
    success_url = reverse_lazy('user_edit')

    def get_initial(self):
        return {
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
        }

    def form_valid(self, form):
        self.request.user.first_name = form.cleaned_data['first_name']
        self.request.user.last_name = form.cleaned_data['last_name']
        self.request.user.save()

        messages.add_message(self.request, messages.SUCCESS, u'Профиль успешно изменён')

        return super(EditFormView, self).form_valid(form)


class SignupFormView(FormView):
    form_class = SignupForm
    template_name = 'users/signup.html'

    def form_valid(self, form):
        signup = UserSignup.objects.signup(form.cleaned_data)

        # Авторизовываем
        from django.contrib.auth import authenticate, login
        user = authenticate(email=signup.email, password=form.cleaned_data['password'])
        if user is not None:
            login(self.request, user)
            messages.add_message(self.request, messages.INFO, u'Мы отправили Вам письмо на <b>{0}</b> для подтверждения активации.'.format(user.email), extra_tags='safe')

        self.success_url = reverse_lazy('user', args=(user.id,))

        return super(SignupFormView, self).form_valid(form)


class ActivationView(TemplateView):
    http_method_names = ['get']
    template_name = 'users/activation.html'

    def get(self, request, *args, **kwargs):
        if UserSignup.objects.activate(**kwargs):
            if self.request.user.is_authenticated():
                self.success_url = reverse_lazy('user', args=(self.request.user.id,))
            else:
                self.success_url = reverse_lazy('login')
            messages.add_message(self.request, messages.SUCCESS, u'Ваш E-mail подтверждён.')
            return redirect(self.success_url)

        return super(ActivationView, self).get(request, *args, **kwargs)


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=LoginForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.user.is_authenticated():
        return redirect(reverse('user', args=(request.user.id,)))

    if request.method == "POST":
        form = authentication_form(request, data=request.POST)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            return redirect(reverse('user', args=(form.get_user().id,)))
    else:
        form = authentication_form(request)

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@sensitive_post_parameters()
@csrf_protect
@login_required
def password_change(request,
                    template_name='registration/password_change_form.html',
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm,
                    current_app=None, extra_context=None):
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u'Пароль успешно изменён')
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@csrf_protect
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=PasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
            }
            if is_admin_site:
                opts = dict(opts, domain_override=request.get_host())

            if get_user_model().objects.get(email=form.cleaned_data['email']).is_active:
                form.save(**opts)
                messages.add_message(request, messages.SUCCESS, u'Ссылка сброса пароля выслана на указанный e-mail')
                form = password_reset_form()
            else:
                messages.add_message(request, messages.ERROR, u'Сначала активируйте аккаунт')
    else:
        form = password_reset_form()
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@sensitive_post_parameters()
@never_cache
def password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        uid = urlsafe_base64_decode(uidb64)
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, u'Пароль успешно изменён')

                if request.user.is_authenticated():
                    return redirect(reverse('user', args=(request.user.id,)))
                else:
                    return redirect(reverse('login'))
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


def logout(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           current_app=None, extra_context=None):
    """
    Logs out the user and displays 'You are logged out' message.
    """
    auth_logout(request)

    if next_page is not None:
        next_page = resolve_url(next_page)

    if redirect_field_name in request.REQUEST:
        next_page = request.REQUEST[redirect_field_name]
        # Security check -- don't allow redirection to a different host.
        if not is_safe_url(url=next_page, host=request.get_host()):
            next_page = request.path

    if next_page:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page)

    current_site = get_current_site(request)
    context = {
        'site': current_site,
        'site_name': current_site.name,
        'title': _('Logged out')
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
        current_app=current_app)