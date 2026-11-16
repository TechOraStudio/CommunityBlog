from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.tokens import email_verification_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='learner1',
            email='learner1@example.com',
            password='Password123!',
            is_email_verified=True
        )

    def test_duplicate_username_or_email_refused(self):
        """FR-2: Duplicate username or email is refused."""
        # Duplicate username
        response = self.client.post(reverse('accounts:register'), {
            'username': 'learner1',
            'email': 'another@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!'
        })
        self.assertFalse(User.objects.filter(email='another@example.com').exists())

        # Duplicate email
        response = self.client.post(reverse('accounts:register'), {
            'username': 'learner2',
            'email': 'learner1@example.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!'
        })
        self.assertFalse(User.objects.filter(username='learner2').exists())

    def test_unverified_user_cannot_login(self):
        """FR-43, FR-44: Unverified user cannot log in."""
        unverified_user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='Password123!',
            is_email_verified=False
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'unverified',
            'password': 'Password123!'
        })
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_verified_user_can_login_and_logout(self):
        """FR-4, FR-5: Verified user can log in and out."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'learner1',
            'password': 'Password123!'
        })
        self.assertTrue('_auth_user_id' in self.client.session)

        # Logout
        response = self.client.post(reverse('accounts:logout'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_email_verification_flow(self):
        """FR-43: Email verification token activates user."""
        unverified_user = User.objects.create_user(
            username='newbie',
            email='newbie@example.com',
            password='Password123!',
            is_email_verified=False
        )
        uid = urlsafe_base64_encode(force_bytes(unverified_user.pk))
        token = email_verification_token.make_token(unverified_user)
        verify_url = reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})

        response = self.client.get(verify_url)
        unverified_user.refresh_from_db()
        self.assertTrue(unverified_user.is_email_verified)

    def test_passwords_are_hashed(self):
        """FR-6, NFR-1: Passwords stored only as hash."""
        user = User.objects.get(username='learner1')
        self.assertNotEqual(user.password, 'Password123!')
        self.assertTrue(user.password.startswith('pbkdf2_') or user.password.startswith('argon2'))
