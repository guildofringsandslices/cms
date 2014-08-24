# -*- coding: utf-8 -*-
from django.shortcuts import render


def base(request):
    return render(request, 'base.html', {})