# -*- coding: utf-8 -*-
from django.contrib import admin

from core.abstracts.admin import RedactorContentAdmin

from apps.articles.models import Article


class ArticleAdmin(RedactorContentAdmin):
    pass

admin.site.register(Article, ArticleAdmin)