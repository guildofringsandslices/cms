# -*- coding: utf-8 -*-
from django.contrib import admin

from core.abstracts.admin import RedactorContentAdmin

from apps.events.models import Event


class EventAdmin(RedactorContentAdmin):
    pass

admin.site.register(Event, EventAdmin)