from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from apps.posts.models import Post, PostStatus, render_markdown
from apps.posts.forms import PostForm
from apps.moderation.models import AdminNotification, NotificationType


@login_required
@require_POST
def post_preview_view(request):
    """Return sanitized Markdown HTML for the author's live post preview."""
    return JsonResponse({'html': render_markdown(request.POST.get('body', ''))})


def post_list_view(request):
    """Public home page showing newest approved posts (FR-21, FR-22, FR-23)."""
    post_qs = Post.objects.filter(status=PostStatus.APPROVED).select_related('author')
    paginator = Paginator(post_qs, 10)  # 10 posts per page (NFR-7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/post_list.html', {'page_obj': page_obj})


def post_detail_view(request, slug):
    """
    Post detail view.
    Approved posts visible to all (FR-21, FR-24).
    Draft/Pending/Rejected visible only to author and admins (FR-22, FR-46).
    """
    post = get_object_or_404(Post.objects.select_related('author', 'reviewed_by'), slug=slug)

    if post.status != PostStatus.APPROVED:
        if not request.user.is_authenticated:
            raise Http404("Post not found.")
        if request.user != post.author and not request.user.is_staff:
            raise Http404("Post not found.")

    return render(request, 'posts/post_detail.html', {'post': post})


@login_required
def post_create_view(request):
    """Create a post as Draft or submit directly for review (FR-8, FR-9)."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        action = request.POST.get('action')
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if action == 'submit':
                post.status = PostStatus.PENDING
                post.save()
                AdminNotification.objects.create(
                    notification_type=NotificationType.POST_SUBMITTED,
                    message=f"New post '{post.title}' submitted for review by {request.user.username}.",
                    post=post,
                    actor_username=request.user.username
                )
                messages.success(request, 'Your post has been submitted for admin review!')
            else:
                post.status = PostStatus.DRAFT
                post.save()
                messages.info(request, 'Post saved as Draft.')
            return redirect('posts:my_posts')
    else:
        form = PostForm()
    return render(request, 'posts/post_form.html', {'form': form, 'title': 'Write a Post'})


@login_required
def post_edit_view(request, slug):
    """
    Edit an existing post (FR-10, FR-12, FR-47, FR-53).
    Only author can edit.
    """
    post = get_object_or_404(Post, slug=slug)

    # FR-12: Refuse edit if not the author
    if post.author != request.user:
        raise PermissionDenied("You can only edit your own posts.")

    initial_status = post.status

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        action = request.POST.get('action')
        if form.is_valid():
            post = form.save(commit=False)

            if initial_status == PostStatus.APPROVED:
                # FR-47 & BR-8: Editing an approved post keeps it approved
                post.is_edited_after_approval = True
                post.edited_at = timezone.now()
                post.save()
                AdminNotification.objects.create(
                    notification_type=NotificationType.POST_EDITED,
                    message=f"Approved post '{post.title}' was edited by author {request.user.username}.",
                    post=post,
                    actor_username=request.user.username
                )
                messages.success(request, 'Post updated successfully.')
                return redirect('posts:post_detail', slug=post.slug)

            elif initial_status == PostStatus.REJECTED:
                # FR-53: Resubmitting a rejected post makes it pending
                if action == 'submit':
                    post.status = PostStatus.PENDING
                    post.rejection_reason = ''
                    post.save()
                    AdminNotification.objects.create(
                        notification_type=NotificationType.POST_SUBMITTED,
                        message=f"Rejected post '{post.title}' was resubmitted by {request.user.username}.",
                        post=post,
                        actor_username=request.user.username
                    )
                    messages.success(request, 'Post resubmitted for admin review.')
                else:
                    post.status = PostStatus.DRAFT
                    post.save()
                    messages.info(request, 'Post saved as Draft.')
                return redirect('posts:my_posts')

            else:  # Was DRAFT or PENDING
                if action == 'submit':
                    post.status = PostStatus.PENDING
                    post.save()
                    AdminNotification.objects.create(
                        notification_type=NotificationType.POST_SUBMITTED,
                        message=f"Post '{post.title}' submitted for review by {request.user.username}.",
                        post=post,
                        actor_username=request.user.username
                    )
                    messages.success(request, 'Post submitted for admin review.')
                else:
                    post.status = PostStatus.DRAFT
                    post.save()
                    messages.info(request, 'Post saved as Draft.')
                return redirect('posts:my_posts')
    else:
        form = PostForm(instance=post)

    return render(request, 'posts/post_form.html', {
        'form': form,
        'post': post,
        'title': f'Edit "{post.title}"'
    })


@login_required
def post_delete_view(request, slug):
    """Delete a post (FR-11, FR-12, FR-19)."""
    post = get_object_or_404(Post, slug=slug)

    # Permission: Author or Admin
    if post.author != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to delete this post.")

    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.success(request, f'Post "{title}" has been deleted.')
        if request.user.is_staff and post.author != request.user:
            return redirect('moderation:dashboard')
        return redirect('posts:my_posts')

    return render(request, 'posts/post_delete_confirm.html', {'post': post})


@login_required
def my_posts_view(request):
    """User dashboard listing own posts by status (FR-13, FR-14, FR-46)."""
    status_filter = request.GET.get('status', '').upper()
    posts_qs = Post.objects.filter(author=request.user)

    if status_filter in PostStatus.values:
        posts_qs = posts_qs.filter(status=status_filter)

    return render(request, 'posts/my_posts.html', {
        'posts': posts_qs,
        'status_filter': status_filter,
        'PostStatus': PostStatus,
    })
