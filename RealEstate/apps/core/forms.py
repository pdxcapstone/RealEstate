from django import forms
from django.contrib.auth.forms import UserCreationForm

from RealEstate.apps.core.models import User, Category


class AddCategoryForm(forms.Form):
    summary = forms.CharField(max_length=100)
    description = forms.CharField(max_length=200)
    
    
class EditCategoryForm(forms.Form):
    summary = forms.CharField(max_length=100)
    description = forms.CharField(max_length=200)
    catID = forms.CharField(widget=forms.HiddenInput())


class EvaluationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        graded = kwargs.pop('graded', [])
        super(EvaluationForm, self).__init__(*args, **kwargs)
        for c, s in graded:
            self.fields[str(c.id)] = forms.CharField(
                initial=s, widget=forms.HiddenInput())


class UserCreationForm(UserCreationForm):
    """
    Overrides the default admin add form to use email instead of username.
    """
    class Meta:
        model = User
        fields = ('email',)
