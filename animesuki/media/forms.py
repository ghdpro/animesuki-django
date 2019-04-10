"""AnimeSuki Media forms"""

from django import forms

from .models import Media, MediaArtwork


class MediaCreateForm(forms.ModelForm):
    comment = forms.CharField(label='Comment / Source')

    class Meta:
        model = Media
        fields = ['title', 'media_type', 'sub_type', 'status', 'is_adult',
                  'episodes', 'duration', 'volumes', 'chapters',
                  'start_date', 'start_precision', 'end_date', 'end_precision',
                  'season_year', 'season', 'description', 'synopsis']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'synopsis': forms.Textarea(attrs={'rows': 2})
        }


class MediaUpdateForm(MediaCreateForm):
    pass


class MediaArtworkForm(forms.ModelForm):

    class Meta:
        model = MediaArtwork
        fields = ['image']


MediaArtworkFormset = forms.models.inlineformset_factory(Media, MediaArtwork, form=MediaArtworkForm,
                                                         extra=1, can_delete=True)
