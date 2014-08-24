# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import user_passes_test, login_required


def active_required(view_func):
    """Чтобы не давать пользователю реально что-то делать до тех пор, пока он не подтвердит e-mail"""
    active = user_passes_test(lambda u: u.is_active, login_url='/profile/not_active')
    return login_required(active(view_func))