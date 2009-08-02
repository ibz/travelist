from django import forms

from travelist import models
from travelist import ui

class PlaceInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if not attrs:
            attrs = {}
        attrs['class'] = 'text'
        if value:
            loc = models.Place.objects.get(id=value)
            loc_id, loc_name = loc.id, loc.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type="text" value="%(loc_name)s" id="id_%(name)s_name"%(attrs)s />
<input type="hidden" value="%(loc_id)s" name="%(name)s" />
<script type="text/javascript">
autoCompletePlace("#id_%(name)s_name", "#id_%(name)s", null);
</script>
"""
            % {'loc_name': loc_name,
               'loc_id': loc_id,
               'name': name,
               'attrs': attrs and forms.util.flatatt(attrs) or ""})

class PlaceChoiceField(forms.fields.ChoiceField):
    def __init__(self, required=True, widget=PlaceInput, label=None, initial=None, help_text=None, *args, **kwargs):
        forms.fields.Field.__init__(self, required, widget, label, initial, help_text, *args, **kwargs)

    def clean(self, value):
        forms.fields.Field.clean(self, value)
        if value in forms.fields.EMPTY_VALUES:
            return None
        try:
            return models.Place.objects.get(pk=value)
        except models.Place.DoesNotExist:
            raise forms.util.ValidationError(self.error_messages['invalid_choice'])

class SuggestionForm(ui.ModelForm):
    name = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    comments = forms.fields.CharField(widget=forms.widgets.Textarea())

    class Meta:
        model = models.PlaceSuggestion
        fields = ('name', 'comments')

class EditForm(ui.ModelForm):
    wiki_content = forms.fields.CharField(widget=forms.widgets.Textarea(attrs={'class': 'text', 'style': "height: 300px; width: 500px"}), required=False)
    class Meta:
        model = models.Place
        fields = ('wiki_content',)
