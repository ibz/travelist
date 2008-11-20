from django import forms

from backpacked import models

class PlaceInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if value:
            loc = models.Place.objects.get(id=value)
            loc_id, loc_name = loc.id, loc.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type="text" value="%(loc_name)s" id="id_%(name)s_name" />
<input type="hidden" value="%(loc_id)s" name="%(name)s"%(attrs)s />
<script type="text/javascript">
$("#id_%(name)s_name").autocomplete("/place/search/",
    {minChars: 2, matchSubset: false,
     onItemSelect: function(li) { $("#id_%(name)s").attr('value', li.extra[0]); }});
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

