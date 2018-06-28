"""AnimeSuki History forms"""

from django import forms


class HistoryCommentForm(forms.Form):
    comment = forms.CharField(label='Comment / Source', required=False)
