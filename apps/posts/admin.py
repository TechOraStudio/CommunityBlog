from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'is_edited_after_approval', 'created_at', 'reviewed_by')
    list_filter = ('status', 'is_edited_after_approval', 'created_at')
    search_fields = ('title', 'body', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'edited_at')
