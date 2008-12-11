from django import forms
from django.utils import encoding
from django.utils import safestring

class FormExtension(object):
    def as_p(self):
        return self._html_output(u'<p>%(label)s<br />%(field)s%(help_text)s</p>', u"%s", "</p>", u"%s", True)

class Form(FormExtension, forms.Form):
    pass

class ModelForm(FormExtension, forms.ModelForm):
    pass
