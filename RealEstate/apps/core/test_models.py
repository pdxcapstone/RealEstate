from django.contrib.auth.models import User
from django.utils import unittest
import models


class TestStringMethods(unittest.TestCase):
    def test_category(self):
        category = models.Category(summary='test1', description='test description')
        self.assertEquals(category.summary, 'test1')
        self.assertEquals(category.description, 'test description')

    def test_homebuyer(self):
        user = User.objects.create(username='foo', password='foo')
        realtor = models.Realtor.objects.create(user=user)
        couple = models.Couple.objects.create(realtor=realtor)
        homebuyer = models.Homebuyer.objects.create(user=User.objects.create(username='hb', password='hb'),
                                                    couple=couple)
        self.assertIsNotNone(homebuyer.user)

    def test_realtor(self):
        user = User.objects.create(username='foo1', password='foo1')
        realtor = models.Realtor.objects.create(user=user)
        self.assertIsNotNone(realtor.user)


if __name__ == '__main__':
    unittest.main()
