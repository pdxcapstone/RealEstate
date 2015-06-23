from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

__all__ = ['Category', 'CategoryWeight', 'Couple', 'Grade', 'Homebuyer',
           'House', 'Realtor']


class Person(models.Model):
    """
    Abstract model class representing information that is common to both
    Homebuyer and Realtor.
    """
    user = models.OneToOneField('auth.User', verbose_name="User")

    def __unicode__(self):
        return self.user.username

    class Meta:
        abstract = True


class Category(models.Model):
    summary = models.CharField(max_length=128, verbose_name="Summary")
    description = models.TextField(blank=True, verbose_name="Description")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")

    def __unicode__(self):
        return self.summary

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class CategoryWeight(models.Model):
    weight = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                          MaxValueValidator(100)],
                                              help_text="0-100",
                                              verbose_name="Weight")
    homebuyer = models.ForeignKey('core.Homebuyer', verbose_name="Homebuyer")
    category = models.ForeignKey('core.Category', verbose_name="Category")

    def __unicode__(self):
        return u"{homebuyer} gives {category} a weight of {weight}.".format(
                homebuyer=unicode(self.homebuyer),
                category=unicode(self.category),
                weight=weight)

    class Meta:
        verbose_name = "Category Weight"
        verbose_name_plural = "Category Weights"


class Couple(models.Model):
    realtor = models.ForeignKey('core.Realtor', verbose_name="Realtor")

    def __unicode__(self):
        homebuyers = self.homebuyer_set.values_list('user__username', flat=True)
        if not homebuyers:
            homebuyers = ['?', '?']
        elif homebuyers.count() == 1:
            homebuyers = [homebuyers.first(), '?']
        return u" and ".join(homebuyers)

    class Meta:
        verbose_name = "Couple"
        verbose_name_plural = "Couples"


class Grade(models.Model):
    score = models.PositiveSmallIntegerField(
        choices=((1, '1'),
                 (2, '2'),
                 (3, '3'),
                 (4, '4'),
                 (5, '5')),
        default=3,
        verbose_name="Score")

    house = models.ForeignKey('core.House', verbose_name="House")
    category = models.ForeignKey('core.Category', verbose_name="Category")
    homebuyer = models.ForeignKey('core.Homebuyer', verbose_name="Homebuyer")

    def __unicode__(self):
        return (u"{homebuyer} gives {house} a score of {score} for category: "
                "{category}.".format(homebuyer=unicode(self.homebuyer),
                                     house=unicode(self.house),
                                     score=self.score,
                                     category=unicode(self.category)))

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"


class Homebuyer(Person):
    partner = models.OneToOneField('core.Homebuyer', blank=True, null=True,
                                   verbose_name="Partner")
    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category', through='core.CategoryWeight',
                                        verbose_name="Categories")

    class Meta:
        verbose_name = "Homebuyer"
        verbose_name_plural = "Homebuyers"


class House(models.Model):
    nickname = models.CharField(max_length=128, verbose_name="Nickname")
    address = models.TextField(blank=True, verbose_name="Address")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category', through='core.Grade',
                                        verbose_name="Categories")

    def __unicode__(self):
        return self.nickname

    class Meta:
        verbose_name = "House"
        verbose_name_plural = "Houses"


class Realtor(Person):
    class Meta:
        verbose_name = "Realtor"
        verbose_name_plural = "Realtors"
