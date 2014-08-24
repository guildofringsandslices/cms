# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse


class RedactorContentAdmin(admin.ModelAdmin):
    readonly_fields = ('admin_site_url',)
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('admin_title', 'title', 'slug', 'admin_site_url', 'admin_text', 'published',)
    list_editable = ('title', 'slug', 'published',)
    list_display_links = ('admin_title',)
    search_fields = ('title', 'slug',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'admin_site_url', 'text', 'published')
        }),
    )

    def admin_title(self, obj):
        """Добавляем self.title в list_editable"""
        return obj.title
    admin_title.short_description = u'Редактировать'

    def admin_text(self, obj):
        """Отображаем обрезанный self.text в list_display"""
        return obj.text[0:70] + u'...' if len(obj.text) > 70 else obj.text
    admin_text.short_description = u'Текст'

    def admin_site_url(self, obj):
        """Чтобы дать ссылку на сайт из админки"""
        return u'<a href="{0}">{0}</a>'.format(reverse('articles.detail', args=(obj.slug,))) if obj.id else u'Пока нет'
    admin_site_url.allow_tags = True
    admin_site_url.short_description = u'Ссылка на сайт'