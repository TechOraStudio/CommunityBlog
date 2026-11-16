from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        if self.is_superuser or self.is_staff:
            self.is_email_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
