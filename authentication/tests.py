from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationEmailTests(TestCase):
    def test_signup_sends_activation_email_and_keeps_account_inactive(self):
        response = self.client.post(reverse('signup'), {
            'username': 'new-seller',
            'email': 'new-seller@example.com',
            'password1': 'Safe-Long-Passphrase-742!',
            'password2': 'Safe-Long-Passphrase-742!',
        })

        self.assertRedirects(response, reverse('signup-success'))
        user = get_user_model().objects.get(username='new-seller')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('activate', mail.outbox[0].body)
