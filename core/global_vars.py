from django.shortcuts import render, redirect, get_object_or_404

from core.models import Setting


def global_vars(request):
    return {
        'site': Setting.objects.all()[0] if Setting.objects.count() > 0 else None,
        'events': range(0,10)
    }