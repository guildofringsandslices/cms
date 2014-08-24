# -*- coding: utf-8 -*-

from django.db import models

from core.abstracts.models import RedactorContent


class Article(RedactorContent):

    class Meta:
        verbose_name = u'статья'
        verbose_name_plural = u'статьи'
