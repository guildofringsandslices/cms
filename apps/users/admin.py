# -*- coding: utf-8 -*-
from django.contrib import admin
from apps.users.models import User, UserSignup


class UserAdmin(admin.ModelAdmin):
    pass
admin.site.register(User, UserAdmin)


class UserSignupAdmin(admin.ModelAdmin):
    pass
admin.site.register(UserSignup, UserSignupAdmin)