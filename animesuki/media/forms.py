"""AnimeSuki Media forms"""

from django import forms

from .models import Media


class MediaCreateUpdateForm(forms.ModelForm):
    comment = forms.CharField(label='Comment / Source')

    class Meta:
        model = Media
        fields = ['title', 'slug', 'media_type', 'sub_type', 'status', 'is_adult',
                  'episodes', 'duration', 'volumes', 'chapters',
                  'start_date', 'start_precision', 'end_date', 'end_precision',
                  'season_year', 'season', 'description', 'synopsis']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'synopsis': forms.Textarea(attrs={'rows': 2})
        }
