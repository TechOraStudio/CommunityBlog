from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    register_view,
    verify_email_view,
    resend_verification_view,
    login_view,
    logout_view,
    profile_edit_view,
    profile_view,
    delete_account_view,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('verify/<str:uidb64>/<str:token>/', verify_email_view, name='verify_email'),
    path('resend-verification/', resend_verification_view, name='resend_verification'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('delete-account/', delete_account_view, name='delete_account'),

    # Password Reset (FR-52)
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.txt',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<str:uidb64>/<str:token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
