# -*- coding: utf-8 -*-

from django.db import models

from core.abstracts.models import RedactorContent


class Event(RedactorContent):

    class Meta:
        verbose_name = u'событие'
        verbose_name_plural = u'события'


class EventDate(models.Model):
    event = models.ForeignKey(Event)
    datetime = models.DateTimeField()