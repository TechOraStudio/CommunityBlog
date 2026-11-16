from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_email_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LearnThread Info', {'fields': ('is_email_verified', 'bio')}),
    )
