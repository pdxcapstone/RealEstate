from django.test import TestCase

from RealEstate.apps.core.models import Realtor, User
from RealEstate.apps.pending.forms import InviteHomebuyerForm, SignupForm
from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer


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
    @classmethod
    def setUpClass(cls):
        super(SignupFormTest, cls).setUpClass()
        cls.invalid_token = 'x' * 64
        cls.user = User.objects.create(email='user@user.com', password='user')
        cls.realtor_user = User.objects.create(email='r@r.com', password='r')
        cls.realtor = Realtor.objects.create(user=cls.realtor_user)
        cls.pending_couple = PendingCouple.objects.create(realtor=cls.realtor)
        cls.pending_homebuyer = PendingHomebuyer.objects.create(
            email='hb@hb.com',
            pending_couple=cls.pending_couple)

    @classmethod
    def tearDownClass(cls):
        cls.pending_homebuyer.delete()
        cls.pending_couple.delete()
        cls.realtor.delete()
        cls.realtor_user.delete()
        cls.user.delete()
        super(SignupFormTest, cls).tearDownClass()

    def test_empty_form_invalid(self):
        form = SignupForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('registration_token', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_email_already_exists_invalid(self):
        form = SignupForm({'email': 'user@user.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registration_token_nonexistent_invalid(self):
        form = SignupForm({
            'registration_token': 'x' * 64
        })
        self.assertFalse(form.is_valid())
        self.assertIn('registration_token', form.errors)

    def test_new_email_matching_token_valid(self):
        form = SignupForm({
            'registration_token': self.pending_homebuyer.registration_token,
            'email': 'new@new.com',
            'first_name': 'f',
            'last_name': 'l',
        })
        self.assertTrue(form.is_valid())
