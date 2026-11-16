from django import forms
from apps.posts.models import Post, PostDirection, PostFont


class PostForm(forms.ModelForm):
    content_font = forms.ChoiceField(
        choices=PostFont.choices,
        initial=PostFont.SANS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    content_direction = forms.ChoiceField(
        choices=PostDirection.choices,
        initial=PostDirection.AUTO,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Post
        fields = ('title', 'body', 'content_font', 'content_direction', 'image', 'video')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter a descriptive title...'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 12,
                'placeholder': 'Write your notes or tutorial in Markdown format (supports **bold**, `code`, lists)...'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'video': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'video/*'
            }),
        }
        help_texts = {
            'body': 'Supports Markdown formatting: **bold**, *italic*, # Headers, `inline code`, ```code blocks```, and bullet lists.',
            'content_font': 'Choose a font that suits your writing language.',
            'content_direction': 'Use right-to-left for Urdu or Arabic, or automatic to detect direction.',
            'image': 'Optional image upload (JPG, PNG, GIF, WEBP).',
            'video': 'Optional video upload (MP4, MOV, AVI, WEBM, MKV).'
        }

    def clean_content_font(self):
        return self.cleaned_data.get('content_font') or PostFont.SANS

    def clean_content_direction(self):
        return self.cleaned_data.get('content_direction') or PostDirection.AUTO
