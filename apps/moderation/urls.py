from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('pending/', views.pending_posts_view, name='pending_posts'),
    path('review/<slug:slug>/', views.review_post_view, name='review_post'),
    path('recently-edited/', views.recently_edited_view, name='recently_edited'),
    path('recently-edited/<slug:slug>/dismiss/', views.dismiss_edited_flag_view, name='dismiss_edited_flag'),
    path('notifications/', views.notification_log_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('users/', views.user_management_view, name='users'),
    path('users/<int:user_id>/toggle/', views.toggle_user_active_view, name='toggle_user_active'),
]
