# -*- coding: utf-8 -*-

from django.db.models import Field
from django.forms import BaseForm


def main():

    ################################################################################
    ### OrderedDict
    ################################################################################

    def extra(self, **kwargs):
        """Метод для models.Field, расширяющий поля методом extra() для доп. параметров"""
        if 'group' in kwargs:
            lol = kwargs.pop('group')
            self.group = lol
        return self
    Field.group = 'default'
    Field.extra = extra

    def as_div(self):
        "Returns this form rendered as HTML <div>s."
        return self._html_output(
            normal_row='<div%(html_class_attr)s data-class="filter__field">%(label)s %(field)s%(help_text)s</div>',
            error_row='%s',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True)
    BaseForm.as_div = as_div

    def as_div_checkbox(self):
        """Меняем label с field местами для адекватного рендеринга чекбоксов."""
        return self._html_output(
            normal_row='<div%(html_class_attr)s data-class="filter__field">%(field)s %(label)s %(help_text)s</div>',
            error_row='%s',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True)
    BaseForm.as_div_checkbox = as_div_checkbox

    def as_table(self):
        """Добавляем div в ячейки, чтобы детям можно было ставить position:absolute
           Для более крутой катомизации форм читаем: http://habrahabr.ru/post/95681/"""
        return self._html_output(
            normal_row='<tr%(html_class_attr)s><th>%(label)s</th><td><div>%(field)s%(errors)s%(help_text)s</div></td></tr>',
            error_row='<tr><td colspan="2">%s</td></tr>',
            row_ender='</td></tr>',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=False,
        )
    BaseForm.as_table = as_table
    BaseForm.required_css_class = 'required'
    BaseForm.error_css_class = 'error'

if __name__ == "__main__":
    main()