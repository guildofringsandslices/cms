# -*- coding: utf-8 -*-

import hashlib
import random
import os
import datetime
import re
import string

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, BaseUserManager
from django.utils import timezone
from django.utils.http import urlquote
from django.core.mail import send_mail
from django.conf import settings

from core.models import Setting

ACTIVATION_CODE_REGEX = '[' + string.hexdigits + ']{32}'


class UserManager(BaseUserManager):

    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()

        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True, unique=True)
    is_staff = models.BooleanField(_('staff status'), default=False, help_text=_('Designates whether the customuser can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_('Designates whether this customuser should be treated as active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _(u'пользователь')
        verbose_name_plural = _(u'пользователи')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def get_username(self):
        "Return the identifying username for this User"
        return self.email

    def get_short_name(self):
        "Return the identifying username for this User"
        return self.email


class UserSignupManager(models.Manager):
    def activate(self, activation_code):
        if re.match(ACTIVATION_CODE_REGEX, activation_code):
            try:
                signup = self.get(activation_code=activation_code)
            except self.model.DoesNotExist:
                return None

            user = signup.user
            user.is_active = True
            user.save()
            signup.delete()
            return user
        return None

    def activate_email(self, user):
        email = user.email

        if isinstance(email, unicode):
            email = email.encode('utf-8')
        salt = os.urandom(256)

        # Убиваем старый сайнап
        if hasattr(user, 'signup'):
            user.signup.delete()

        signup = self.create(user=user, activation_code=hashlib.sha256(email + salt).hexdigest()[:32])

        signup.send_activation_email()

    def signup(self, cleaned_data):
        user_model = get_user_model()
        user_fields = {}
        for field in user_model._meta.get_all_field_names():
            if field in cleaned_data:
                user_fields[field] = cleaned_data[field]
        user = user_model.objects.create_user(**user_fields)
        user.is_active = False
        user.save()

        self.activate_email(user)

        return user

    signup = transaction.commit_on_success(signup)  # TODO: Что это и чем нужно заменить?


class UserSignup(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, unique=True, related_name='signup')
    activation_code = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    #email = models.CharField(max_length=255)

    objects = UserSignupManager()

    def send_activation_email(self):
        site = Setting.objects.all()[0] if Setting.objects.count() > 0 else None
        context = {'activation_code': self.activation_code, 'site': site, 'protocol': 'http'}
        subject = ' '.join(render_to_string('users/activation_email/activation_email_subject.txt', context).splitlines())
        message = render_to_string('users/activation_email/activation_email_message.html', context)
        self.user.email_user(subject, message)

    class Meta:
        verbose_name = _(u'активация')
        verbose_name_plural = _(u'активации')

    def __unicode__(self):
        return self.user.email