# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404

from apps.articles.models import Article


# login required
def event_new(request):
    pass


# login required
def event_edit(request):
    pass


# login required
def event_delete(request):
    pass


def event_list(request):
    return render(request, 'events/event_list.html', {
        'object': Article,
        'objects': Article.objects.filter(published=True)
    })


def event_detail(request, slug):
    return render(request, 'events/event_detail.html', {
        'object': get_object_or_404(Article, **{'slug': slug, 'published': True})
    })