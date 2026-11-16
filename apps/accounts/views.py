from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from apps.accounts.models import User
from apps.accounts.forms import RegisterForm, LoginForm, ProfileForm, ResendVerificationForm
from apps.accounts.tokens import email_verification_token
from apps.moderation.models import AdminNotification, NotificationType
from apps.posts.models import PostStatus


def send_verification_email(request, user):
    """Generate email verification link and send email to user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    subject = 'Verify your email address - LearnThread'
    message = (
        f"Hi {user.username},\n\n"
        f"Thank you for joining LearnThread!\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"If you did not create this account, you can safely ignore this email.\n"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )


def register_view(request):
    """Visitor registration view (FR-1, FR-2, FR-43)."""
    if request.user.is_authenticated:
        return redirect('posts:post_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = False
            user.save()
            send_verification_email(request, user)
            messages.success(
                request,
                'Registration successful! We have sent a verification email to your address. '
                'Please verify your email before logging in.'
            )
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email_view(request, uidb64, token):
    """Email verification link handler (FR-43, FR-44)."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, 'Your email has been successfully verified! You can now log in.')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
    return redirect('accounts:login')


def resend_verification_view(request):
    """Resend verification email view (FR-45)."""
    if request.method == 'POST':
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            if user:
                if user.is_email_verified:
                    messages.info(request, 'This email address is already verified. You can log in.')
                    return redirect('accounts:login')
                send_verification_email(request, user)
            messages.success(request, 'If an account exists with this email, a verification link has been sent.')
            return redirect('accounts:login')
    else:
        form = ResendVerificationForm()
    return render(request, 'accounts/resend_verification.html', {'form': form})


def login_view(request):
    """User login view (FR-4, FR-44)."""
    if request.user.is_authenticated:
        return redirect('posts:post_list')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next') or 'posts:post_list'
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view (FR-5)."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'You have been logged out.')
    return redirect('posts:post_list')


@login_required
def profile_edit_view(request):
    """Edit own profile (FR-41)."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


def profile_view(request, username):
    """Public user profile page with approved posts (FR-40)."""
    profile_user = get_object_or_404(User, username=username)
    approved_posts = profile_user.posts.filter(
        status=PostStatus.APPROVED
    ).order_by('-created_at')
    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'posts': approved_posts
    })


@login_required
def delete_account_view(request):
    """Delete own account with cascading deletion of all user data (FR-48, FR-49, FR-56, FR-57)."""
    if request.method == 'POST':
        username = request.user.username
        AdminNotification.objects.create(
            notification_type=NotificationType.ACCOUNT_DELETED,
            message=f"User '{username}' deleted their account.",
            actor_username=username
        )
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account and all associated posts have been permanently deleted.')
        return redirect('posts:post_list')
    return render(request, 'accounts/account_delete_confirm.html')
