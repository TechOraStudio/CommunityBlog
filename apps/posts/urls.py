from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.post_list_view, name='post_list'),
    path('write/', views.post_create_view, name='post_create'),
    path('my-posts/', views.my_posts_view, name='my_posts'),
    path('post/<slug:slug>/', views.post_detail_view, name='post_detail'),
    path('post/<slug:slug>/edit/', views.post_edit_view, name='post_edit'),
    path('post/<slug:slug>/delete/', views.post_delete_view, name='post_delete'),
]
