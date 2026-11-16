from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from apps.accounts.models import User
from apps.accounts.tokens import email_verification_token


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
            'password1': 'Password123!',
            'password2': 'Password123!'
        })
        self.assertFalse(User.objects.filter(email='another@example.com').exists())

        # Duplicate email
        response = self.client.post(reverse('accounts:register'), {
            'username': 'learner2',
            'email': 'learner1@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!'
        })
        self.assertFalse(User.objects.filter(username='learner2').exists())

    @override_settings(AUTO_VERIFY_EMAILS=False)
    def test_registration_sends_verification_and_user_can_verify_then_login(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newauthor',
            'email': 'newauthor@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        })

        self.assertRedirects(response, reverse('accounts:login'))
        new_user = User.objects.get(username='newauthor')
        self.assertFalse(new_user.is_email_verified)
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('accounts/verify/', mail.outbox[0].body)

        verification_path = mail.outbox[0].body.splitlines()[5]
        verify_response = self.client.get(verification_path)
        self.assertRedirects(verify_response, reverse('accounts:login'))
        new_user.refresh_from_db()
        self.assertTrue(new_user.is_email_verified)

        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'newauthor',
            'password': 'SecurePass123!'
        })
        self.assertRedirects(login_response, reverse('posts:post_list'))
        self.assertEqual(str(self.client.session['_auth_user_id']), str(new_user.pk))

    @override_settings(AUTO_VERIFY_EMAILS=False)
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

    @override_settings(AUTO_VERIFY_EMAILS=True)
    def test_local_registration_auto_verifies_and_allows_login(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'localauthor',
            'email': 'localauthor@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!'
        })

        self.assertRedirects(response, reverse('accounts:login'))
        new_user = User.objects.get(username='localauthor')
        self.assertTrue(new_user.is_email_verified)
        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)

        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'localauthor',
            'password': 'SecurePass123!'
        })
        self.assertRedirects(login_response, reverse('posts:post_list'))

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

    def test_login_rejects_external_next_url(self):
        response = self.client.post(
            reverse('accounts:login') + '?next=https://example.com/',
            {'username': 'learner1', 'password': 'Password123!'}
        )

        self.assertRedirects(response, reverse('posts:post_list'))

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

    def test_user_can_upload_profile_photo(self):
        """Profile photos can be attached to a user account."""
        photo = SimpleUploadedFile('avatar.png', b'fake-image-content', content_type='image/png')
        self.user.profile_photo = photo
        self.user.save()

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_photo.name.endswith('.png'))

    def test_passwords_are_hashed(self):
        """FR-6, NFR-1: Passwords stored only as hash."""
        user = User.objects.get(username='learner1')
        self.assertNotEqual(user.password, 'Password123!')
        self.assertTrue(user.password.startswith('pbkdf2_') or user.password.startswith('argon2'))
