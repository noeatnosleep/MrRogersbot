__author__ = 'Aaron'
from django import forms
from models import SubSettings

#class Settings(forms.Form):
#    removalreason = forms.Textarea(label = "Enter Removal Reason",initial="This Data")

class SettingsForm(forms.ModelForm):
    class Meta:
        model = SubSettings
        exclude = ['']

