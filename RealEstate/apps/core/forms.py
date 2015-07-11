from django import forms
from django.contrib.auth.forms import UserCreationForm

from RealEstate.apps.core.models import User


class ContactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        graded = kwargs.pop('graded', [])
        #default_score = kwargs.pop('default_score')
        super(ContactForm, self).__init__(*args, **kwargs)
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
