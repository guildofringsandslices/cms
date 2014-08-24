# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'core.views.base', name='base'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/', include('apps.users.urls')),
    url(r'^articles/$', 'apps.articles.views.article_list', name='articles.list'),
    url(r'^(?P<slug>.+)/$', 'apps.articles.views.article_detail', name='articles.detail'),
)

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
