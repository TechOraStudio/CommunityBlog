from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='A verification link will be sent to this email address.'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with that email already exists.')
        return email


class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        # Superusers and staff bypass email verification
        if not user.is_email_verified and not (user.is_superuser or user.is_staff):
            raise ValidationError(
                'Your email address is not verified yet. Please check your inbox or request a new verification email.',
                code='unverified_email'
            )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'bio')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell the community about yourself...'}),
        }


class ResendVerificationForm(forms.Form):
    email = forms.EmailField(required=True)
