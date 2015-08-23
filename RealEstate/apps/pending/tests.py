from django.test import TestCase

from RealEstate.apps.core.models import User
from RealEstate.apps.pending.forms import (HomebuyerSignupForm,
                                           InviteHomebuyerForm)


class HomebuyerSignupFormTest(TestCase):
    def test_empty_form_invalid(self):
        form = HomebuyerSignupForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('password_confirmation', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_passwords_dont_match_invalid(self):
        form = HomebuyerSignupForm({
            'password': 'foo',
            'password_confirmation': 'bar',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirmation', form.errors)

    def test_matching_token_valid(self):
        form = HomebuyerSignupForm({
            'password': 'foo',
            'password_confirmation': 'foo',
            'first_name': 'f',
            'last_name': 'l',
        })
        self.assertTrue(form.is_valid())


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
        self.assertIn('email', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_incorrect_email_format_invalid(self):
        form = InviteHomebuyerForm({
            'email': 'FOO',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_user_already_exists_invalid(self):
        form = InviteHomebuyerForm({
            'email': 'user@user.com',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_valid_email_and_name_valid(self):
        form = InviteHomebuyerForm({
            'email': 'test1@test1.com',
            'first_name': 'first',
            'last_name': 'last',
        })
        self.assertTrue(form.is_valid())
