from django import forms
from django.contrib.auth.forms import UserCreationForm

from RealEstate.apps.core.models import User, Category


DEFAULT_CHOICE_LIST = (
    ('yard', 'Yard'),
    ('kitchen', 'Kitchen'),
    ('square-footage', 'Square Footage'),
)


class AddCategoryForm(forms.Form):
    default_choices = forms.MultipleChoiceField(label="Choose from the list or create your own category below.", required=False,
        widget=forms.CheckboxSelectMultiple, choices=DEFAULT_CHOICE_LIST)
    summary = forms.CharField(required=False, max_length=100)
    description = forms.CharField(required=False, max_length=200)
    

class EditCategoryForm(forms.Form):
    edit_summary = forms.CharField(label='Summary', max_length=100)
    edit_description = forms.CharField(required=False, label='Description', max_length=200)
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

