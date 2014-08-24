# -*- coding: utf-8 -*-
import json

from collections import OrderedDict
from django.db import models
from django.utils.text import mark_safe
from django.utils.html import escape


class Content(models.Model):

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title if hasattr(self, 'title') else str(self.id)

    def meta(self):
        return self._meta

    def app_object_name(self):
        """Чтобы построить ссылки на админку в templates/core/admin_links.html"""
        return self._meta.app_label.lower() + '_' + self._meta.object_name.lower()

    def dump(self):

        fields = OrderedDict()

        # Поля models
        for field in self._meta.fields:
            string = field.value_to_string(self)
            fields[field.name] = string[0:70] + u'...' if len(string) > 70 else string

        # Meta
        fields['meta.verbose_name'] = self._meta.verbose_name
        fields['meta.verbose_name_plural'] = self._meta.verbose_name_plural

        # Дополнительно
        fields['app_object_name'] = self.app_object_name()

        return mark_safe(u'<pre>{0}</pre>'.format(escape(json.dumps(fields, ensure_ascii=False, indent=4))))


class RedactorContent(Content):
    title = models.CharField(verbose_name=u'Заголовок', max_length=255)
    slug = models.CharField(verbose_name=u'Ссылка', max_length=255, unique=True)
    text = models.TextField(verbose_name=u'Текст', blank=True, null=True)
    published = models.BooleanField(verbose_name=u'Опубликован', default=True)

    class Meta:
        abstract = True