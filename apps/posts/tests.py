from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.posts.models import Post, PostStatus
from apps.moderation.models import AdminNotification

User = get_user_model()


class PostsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author1 = User.objects.create_user(
            username='author1',
            email='author1@example.com',
            password='Password123!',
            is_email_verified=True
        )
        self.author2 = User.objects.create_user(
            username='author2',
            email='author2@example.com',
            password='Password123!',
            is_email_verified=True
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='Password123!',
            is_email_verified=True
        )

    def test_visitor_blocked_from_writing(self):
        """FR-7: Visitor redirected to login when trying to access write-post."""
        response = self.client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_post_creation_draft_and_pending(self):
        """FR-8, FR-9: Save as draft or submit as pending."""
        self.client.force_login(self.author1)

        # Save draft
        self.client.post(reverse('posts:post_create'), {
            'title': 'My Draft Note',
            'body': 'This is draft content.',
            'action': 'draft'
        })
        draft = Post.objects.get(title='My Draft Note')
        self.assertEqual(draft.status, PostStatus.DRAFT)

        # Submit pending
        self.client.post(reverse('posts:post_create'), {
            'title': 'My Pending Tutorial',
            'body': 'Learning Django step by step.',
            'action': 'submit'
        })
        pending = Post.objects.get(title='My Pending Tutorial')
        self.assertEqual(pending.status, PostStatus.PENDING)

    def test_public_cannot_see_draft_or_pending(self):
        """FR-21, FR-22, FR-46: Public list and detail hide unapproved posts."""
        draft = Post.objects.create(title='Draft X', body='Draft', author=self.author1, status=PostStatus.DRAFT)
        pending = Post.objects.create(title='Pending Y', body='Pending', author=self.author1, status=PostStatus.PENDING)
        approved = Post.objects.create(title='Approved Z', body='Approved', author=self.author1, status=PostStatus.APPROVED)

        # Public list
        response = self.client.get(reverse('posts:post_list'))
        self.assertContains(response, 'Approved Z')
        self.assertNotContains(response, 'Draft X')
        self.assertNotContains(response, 'Pending Y')

        # Visitor detail access
        self.assertEqual(self.client.get(reverse('posts:post_detail', kwargs={'slug': approved.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('posts:post_detail', kwargs={'slug': draft.slug})).status_code, 404)
        self.assertEqual(self.client.get(reverse('posts:post_detail', kwargs={'slug': pending.slug})).status_code, 404)

    def test_permission_refuses_cross_user_edit_or_delete(self):
        """FR-12, NFR-4: User A cannot edit or delete User B's post."""
        post_b = Post.objects.create(title='User B Post', body='Content', author=self.author2, status=PostStatus.APPROVED)

        self.client.force_login(self.author1)

        # Attempt edit
        response = self.client.get(reverse('posts:post_edit', kwargs={'slug': post_b.slug}))
        self.assertEqual(response.status_code, 403)

        # Attempt delete
        response = self.client.post(reverse('posts:post_delete', kwargs={'slug': post_b.slug}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=post_b.pk).exists())

    def test_approved_post_editing_keeps_approved_and_flags_edited(self):
        """FR-47, BR-8: Editing an approved post keeps it approved and flags it."""
        post = Post.objects.create(title='Original Title', body='Body', author=self.author1, status=PostStatus.APPROVED)
        self.client.force_login(self.author1)

        response = self.client.post(reverse('posts:post_edit', kwargs={'slug': post.slug}), {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'action': 'submit'
        })
        post.refresh_from_db()
        self.assertEqual(post.status, PostStatus.APPROVED)
        self.assertTrue(post.is_edited_after_approval)
        self.assertIsNotNone(post.edited_at)

    def test_markdown_sanitization_xss(self):
        """FR-54, NFR-3: Markdown rendered safely, script tags prevented."""
        post = Post.objects.create(
            title='Test XSS',
            body='**Bold text** and <script>alert("hacked")</script>',
            author=self.author1,
            status=PostStatus.APPROVED
        )
        rendered = post.rendered_body
        self.assertIn('<strong>Bold text</strong>', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('alert("hacked")', rendered)

    def test_account_deletion_removes_user_posts(self):
        """FR-48, FR-56: Deleting an account deletes all their posts."""
        Post.objects.create(title='Post 1', body='Body 1', author=self.author1, status=PostStatus.APPROVED)
        Post.objects.create(title='Post 2', body='Body 2', author=self.author1, status=PostStatus.DRAFT)

        self.client.force_login(self.author1)
        self.client.post(reverse('accounts:delete_account'))

        self.assertFalse(User.objects.filter(username='author1').exists())
        self.assertEqual(Post.objects.filter(author__username='author1').count(), 0)
