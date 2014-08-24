# -*- coding: utf-8 -*-
from django.contrib import admin
from models import Setting


class SettingsAdmin(admin.ModelAdmin):
    pass
admin.site.register(Setting, SettingsAdmin)