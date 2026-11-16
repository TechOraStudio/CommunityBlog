from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models


class User(AbstractUser):
    """
    Custom user model for CommunityBlog.
    Enforces unique emails, profile photo support, and email verification status.
    """
    email = models.EmailField(unique=True, verbose_name="Email Address")
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name='Profile Photo',
        help_text='Upload a profile photo for your public profile.'
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email Verified",
        help_text="Designates whether this user has confirmed their email address."
    )
    bio = models.TextField(
        blank=True,
        default='',
        verbose_name="Biography",
        help_text="Short bio shown on the public user profile."
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.is_staff = True
        # Superusers and staff are automatically marked as verified
        if self.is_superuser or self.is_staff:
            self.is_email_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
