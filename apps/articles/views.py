# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404

from apps.articles.models import Article


def article_list(request):
    return render(request, 'articles/article_list.html', {
        'object': Article,
        'objects': Article.objects.filter(published=True)
    })


def article_detail(request, slug):
    return render(request, 'articles/article_detail.html', {
        'object': get_object_or_404(Article, **{'slug': slug, 'published': True})
    })