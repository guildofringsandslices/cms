# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from apps.users.views import EditFormView, SignupFormView, ActivationView
from apps.users.models import ACTIVATION_CODE_REGEX

urlpatterns = patterns('',

    url(r'^signup/$', SignupFormView.as_view(), name='signup'),
    url(r'^send_activate/$', 'apps.users.views.send_activate', name='send_activate'),
    url(r'^activate/(?P<activation_code>' + ACTIVATION_CODE_REGEX + r')/$', ActivationView.as_view(), name='activate'),
    url(r'^(?P<user_id>\d+)/', 'apps.users.views.user', name='user'),
    url(r'^edit/$', login_required(EditFormView.as_view()), name='user_edit'),
    url(r'^edit_email/$', 'apps.users.views.edit_email', name='edit_email'),
    url(r'^password/change/$', 'apps.users.views.password_change', {'template_name': 'users/password_change.html'}, name='password_change'),
    url(r'^login/$', 'apps.users.views.login', {'template_name': 'users/login.html'}, name='login'),
    url(r'^logout/$', 'apps.users.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^password/reset/$', 'apps.users.views.password_reset', {'template_name': 'users/password_reset.html', 'email_template_name': 'users/password_reset_email/password_reset_message.html', 'subject_template_name': 'users/password_reset_email/password_reset_subject.txt', 'post_reset_redirect': '/user/password/reset/done/'}, name='password_reset'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', 'apps.users.views.password_reset_confirm', {'template_name': 'users/password_reset_confirm.html'}, name='password_reset_confirm'),

    # TODO: Удалить пользователя
    # TODO: Формы edit, edit_email, password_change - должны быть на одной странице

    url(r'^public_offer/', 'core.views.base', name="public_offer"),
)