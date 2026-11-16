from django.urls import path
from apps.moderation.views import (
    dashboard_view,
    pending_posts_view,
    review_post_view,
    recently_edited_view,
    dismiss_edited_flag_view,
    notification_log_view,
    mark_notification_read_view,
    mark_all_notifications_read_view,
    user_management_view,
    toggle_user_active_view,
)

app_name = 'moderation'

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('pending/', pending_posts_view, name='pending_posts'),
    path('review/<slug:slug>/', review_post_view, name='review_post'),
    path('recently-edited/', recently_edited_view, name='recently_edited'),
    path('recently-edited/<slug:slug>/dismiss/', dismiss_edited_flag_view, name='dismiss_edited_flag'),
    path('notifications/', notification_log_view, name='notifications'),
    path('notifications/<int:pk>/read/', mark_notification_read_view, name='mark_notification_read'),
    path('notifications/read-all/', mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('users/', user_management_view, name='users'),
    path('users/<int:user_id>/toggle/', toggle_user_active_view, name='toggle_user_active'),
]
