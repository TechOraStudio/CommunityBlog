from django.urls import path
from apps.posts.views import (
    post_list_view,
    post_create_view,
    my_posts_view,
    post_detail_view,
    post_edit_view,
    post_delete_view,
)

app_name = 'posts'

urlpatterns = [
    path('', post_list_view, name='post_list'),
    path('write/', post_create_view, name='post_create'),
    path('my-posts/', my_posts_view, name='my_posts'),
    path('post/<slug:slug>/', post_detail_view, name='post_detail'),
    path('post/<slug:slug>/edit/', post_edit_view, name='post_edit'),
    path('post/<slug:slug>/delete/', post_delete_view, name='post_delete'),
]
