from travelist import models
from travelist import ui

class EditForm(ui.ModelForm):
    class Meta:
        model = models.Suggestion
        fields = ('type', 'comments')
