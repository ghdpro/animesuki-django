"""AnimeSuki Media forms"""

from django import forms
from django.utils.text import slugify

from .models import Media


class MediaCreateForm(forms.ModelForm):
    slug = forms.CharField(required=False, help_text='Leave slug empty: it will be generated automatically.')
    comment = forms.CharField(label='Comment / Source')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug').strip()
        if not slug:
            slug = slugify(self.cleaned_data.get('title'))
            # "Monkey patch" the generated slug into form POST data (otherwise it won't be included if form has errors)
            q = self.data.copy()
            q['slug'] = slug
            self.data = q
        return slug

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


class MediaUpdateForm(MediaCreateForm):
    slug = forms.CharField(required=True)
