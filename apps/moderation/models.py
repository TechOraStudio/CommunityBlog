from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    POST_EDITED = 'POST_EDITED', 'Post Edited After Approval'
    ACCOUNT_DELETED = 'ACCOUNT_DELETED', 'Account Deleted'
    POST_SUBMITTED = 'POST_SUBMITTED', 'Post Submitted For Review'


class AdminNotification(models.Model):
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True
    )
    message = models.TextField()
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_notifications'
    )
    actor_username = models.CharField(max_length=150, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.message[:50]}"
