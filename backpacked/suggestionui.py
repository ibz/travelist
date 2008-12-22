from backpacked import models
from backpacked import ui

class EditForm(ui.ModelForm):
    class Meta:
        model = models.Suggestion
        fields = ('type', 'comments')
