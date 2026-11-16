from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'body')
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
        }
        help_texts = {
            'body': 'Supports Markdown formatting: **bold**, *italic*, # Headers, `inline code`, ```code blocks```, and bullet lists.'
        }
