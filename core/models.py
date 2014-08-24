# -*- coding: utf-8 -*-

from django.db import models

from core.abstracts.models import Content


class Setting(Content):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    email = models.CharField(max_length=255)

    class Meta:
        verbose_name = u'настройка'
        verbose_name_plural = u'настройки'