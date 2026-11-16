from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

from apps.accounts.models import User


class RegisterForm(UserCreationForm):
    """User registration form enforcing unique email and password confirmation."""
    email = forms.EmailField(
        required=True,
        help_text='A verification link will be sent to this email address.'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Login form ensuring non-staff accounts must have a verified email."""
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_email_verified or user.is_superuser or user.is_staff:
            return
        if settings.AUTO_VERIFY_EMAILS:
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            return
        raise ValidationError(
            'Your email address is not verified yet. Please check your inbox or request a new verification email.',
            code='unverified_email'
        )


class ProfileForm(forms.ModelForm):
    """Profile editing form for learners."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'profile_photo', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Tell the community about yourself, what you are learning, or your projects...'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'profile_photo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
        }


class ResendVerificationForm(forms.Form):
    """Form to request a fresh email verification link."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'})
    )
