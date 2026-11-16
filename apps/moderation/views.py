from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from apps.accounts.models import User
from apps.posts.models import Post, PostStatus
from apps.moderation.models import AdminNotification, NotificationType


def admin_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(admin_check)
def dashboard_view(request):
    """Overview dashboard for moderation."""
    pending_count = Post.objects.filter(status=PostStatus.PENDING).count()
    edited_count = Post.objects.filter(is_edited_after_approval=True).count()
    unread_notifications = AdminNotification.objects.filter(is_read=False).count()
    users_count = User.objects.count()

    recent_pending = Post.objects.filter(status=PostStatus.PENDING).select_related('author')[:5]
    recent_notifications = AdminNotification.objects.all()[:5]

    return render(request, 'moderation/dashboard.html', {
        'pending_count': pending_count,
        'edited_count': edited_count,
        'unread_notifications': unread_notifications,
        'users_count': users_count,
        'recent_pending': recent_pending,
        'recent_notifications': recent_notifications,
    })


@user_passes_test(admin_check)
def pending_posts_view(request):
    """List of all posts pending moderation (FR-15)."""
    pending_posts = Post.objects.filter(status=PostStatus.PENDING).select_related('author').order_by('created_at')
    return render(request, 'moderation/pending_posts.html', {'posts': pending_posts})


@user_passes_test(admin_check)
def review_post_view(request, slug):
    """Review, approve or reject a post (FR-16, FR-17, FR-18, BR-5)."""
    post = get_object_or_404(Post.objects.select_related('author'), slug=slug)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            post.status = PostStatus.APPROVED
            post.reviewed_by = request.user
            post.reviewed_at = timezone.now()
            post.rejection_reason = ''
            post.save()
            messages.success(request, f'Post "{post.title}" has been APPROVED.')
            return redirect('moderation:pending_posts')

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '').strip()
            if not reason:
                messages.error(request, 'A rejection reason is required (BR-5).')
                return render(request, 'moderation/review_post.html', {'post': post})

            post.status = PostStatus.REJECTED
            post.rejection_reason = reason
            post.reviewed_by = request.user
            post.reviewed_at = timezone.now()
            post.save()
            messages.warning(request, f'Post "{post.title}" has been REJECTED.')
            return redirect('moderation:pending_posts')

    return render(request, 'moderation/review_post.html', {'post': post})


@user_passes_test(admin_check)
def recently_edited_view(request):
    """List of Approved posts edited after approval (FR-47, FR-55)."""
    posts = Post.objects.filter(is_edited_after_approval=True).select_related('author').order_by('-edited_at')
    return render(request, 'moderation/recently_edited.html', {'posts': posts})


@user_passes_test(admin_check)
def dismiss_edited_flag_view(request, slug):
    """Acknowledge and clear the edited-after-approval flag."""
    post = get_object_or_404(Post, slug=slug)
    post.is_edited_after_approval = False
    post.save()
    messages.success(request, f'Edited notice acknowledged for "{post.title}".')
    return redirect('moderation:recently_edited')


@user_passes_test(admin_check)
def notification_log_view(request):
    """Admin notification log with read/unread toggle (FR-57)."""
    notifications_qs = AdminNotification.objects.all().select_related('post')
    paginator = Paginator(notifications_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'moderation/notification_log.html', {'page_obj': page_obj})


@user_passes_test(admin_check)
def mark_notification_read_view(request, pk):
    """Mark a notification as read (FR-57)."""
    notification = get_object_or_404(AdminNotification, pk=pk)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('moderation:notifications')


@user_passes_test(admin_check)
def mark_all_notifications_read_view(request):
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('moderation:notifications')


@user_passes_test(admin_check)
def user_management_view(request):
    """Manage users: view, activate, and deactivate (FR-20)."""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'moderation/user_management.html', {'users': users})


@user_passes_test(admin_check)
def toggle_user_active_view(request, user_id):
    """Deactivate or activate a user account (FR-20)."""
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own account from here.')
        return redirect('moderation:users')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated"
    messages.info(request, f"User '{target_user.username}' has been {status_str}.")
    return redirect('moderation:users')
