from django.test import TestCase

from RealEstate.apps.core.models import User
from RealEstate.apps.pending.forms import InviteHomebuyerForm, SignupForm


class InviteHomebuyerFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(InviteHomebuyerFormTest, cls).setUpClass()
        cls.user = User.objects.create(email='user@user.com', password='user')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        super(InviteHomebuyerFormTest, cls).tearDownClass()

    def test_empty_form_invalid(self):
        form = InviteHomebuyerForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('first_email', form.errors)
        self.assertIn('second_email', form.errors)

    def test_missing_one_email_invalid(self):
        form = InviteHomebuyerForm({'first_email': 'test@test.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('second_email', form.errors)

    def test_incorrect_email_format_invalid(self):
        form = InviteHomebuyerForm({
            'first_email': 'FOO',
            'second_email': 'test@test.com'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('first_email', form.errors)

    def test_email_user_already_exists_invalid(self):
        form = InviteHomebuyerForm({
            'first_email': 'user@user.com',
            'second_email': 'test@test.com'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('first_email', form.errors)

    def test_both_emails_are_the_same_invalid(self):
        form = InviteHomebuyerForm({
            'first_email': 'test@test.com',
            'second_email': 'test@test.com'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_two_new_distinct_emails_valid(self):
        form = InviteHomebuyerForm({
            'first_email': 'test1@test1.com',
            'second_email': 'test2@test2.com'
        })
        self.assertTrue(form.is_valid())


class SignupFormTest(TestCase):
    def test_empty_form_invalid(self):
        form = SignupForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('password_confirmation', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_passwords_dont_match_invalid(self):
        form = SignupForm({
            'password': 'foo',
            'password_confirmation': 'bar',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirmation', form.errors)

    def test_matching_token_valid(self):
        form = SignupForm({
            'password': 'foo',
            'password_confirmation': 'foo',
            'first_name': 'f',
            'last_name': 'l',
        })
        self.assertTrue(form.is_valid())
