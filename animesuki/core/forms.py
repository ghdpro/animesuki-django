"""AnimeSuki Core forms"""

from django import forms


class ArtworkActiveForm(forms.Form):
    active = forms.IntegerField(min_value=1)
