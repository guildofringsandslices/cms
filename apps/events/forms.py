# -*- coding: utf-8 -*-

import datetime
import warnings

from django import forms


class BaseProfileForm(forms.Form):
    required_css_class = 'required'

    first_name = forms.CharField(label=u'Имя')
    last_name = forms.CharField(label=u'Фамилия')

    def clean_first_name(self):
        return self.cleaned_data['first_name'].title()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].title()