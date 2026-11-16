from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.posts.models import Post, PostStatus


class ModerationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.learner = User.objects.create_user(
            username='learner',
            email='learner@example.com',
            password='Password123!',
            is_email_verified=True
        )
        self.moderator = User.objects.create_superuser(
            username='mod1',
            email='mod1@example.com',
            password='Password123!',
            is_email_verified=True
        )
        self.post = Post.objects.create(
            title='Learning Python',
            body='Python is great.',
            author=self.learner,
            status=PostStatus.PENDING
        )

    def test_non_staff_blocked_from_moderation(self):
        """Regular users and visitors cannot access moderation."""
        self.client.force_login(self.learner)
        response = self.client.get(reverse('moderation:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_approves_post(self):
        """FR-16, FR-18: Admin approves pending post, recording admin & timestamp."""
        self.client.force_login(self.moderator)
        response = self.client.post(
            reverse('moderation:review_post', kwargs={'slug': self.post.slug}),
            {'action': 'approve'}
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, PostStatus.APPROVED)
        self.assertEqual(self.post.reviewed_by, self.moderator)
        self.assertIsNotNone(self.post.reviewed_at)

    def test_admin_rejects_post_requires_reason(self):
        """FR-17, BR-5: Admin rejection requires a reason."""
        self.client.force_login(self.moderator)

        # Reject without reason should fail
        response = self.client.post(
            reverse('moderation:review_post', kwargs={'slug': self.post.slug}),
            {'action': 'reject', 'rejection_reason': ''}
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, PostStatus.PENDING)

        # Reject with reason succeeds
        response = self.client.post(
            reverse('moderation:review_post', kwargs={'slug': self.post.slug}),
            {'action': 'reject', 'rejection_reason': 'Please add more code examples.'}
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, PostStatus.REJECTED)
        self.assertEqual(self.post.rejection_reason, 'Please add more code examples.')
        self.assertEqual(self.post.reviewed_by, self.moderator)

    def test_author_resubmits_rejected_post(self):
        """FR-53: Author edits and resubmits rejected post -> becomes Pending."""
        self.post.status = PostStatus.REJECTED
        self.post.rejection_reason = 'Needs more details'
        self.post.save()

        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'slug': self.post.slug}),
            {
                'title': 'Learning Python (Updated)',
                'body': 'Here are the expanded details and code examples.',
                'action': 'submit'
            }
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, PostStatus.PENDING)
        self.assertEqual(self.post.rejection_reason, '')

    def test_admin_deactivates_user(self):
        """FR-20: Admin can deactivate a user."""
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('moderation:toggle_user_active', kwargs={'user_id': self.learner.pk}))
        self.learner.refresh_from_db()
        self.assertFalse(self.learner.is_active)
