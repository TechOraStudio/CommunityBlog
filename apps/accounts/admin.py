from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'is_email_verified',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('is_email_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LearnThread Profile', {'fields': ('is_email_verified', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LearnThread Profile', {'fields': ('email', 'is_email_verified', 'bio')}),
    )
