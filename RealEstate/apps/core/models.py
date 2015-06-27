from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
    """
    Represents a category for a single couple, meaning each couple will define
    their own categories that are important to them rather than every couple
    sharing from the same list.
    """
    summary = models.CharField(max_length=128, verbose_name="Summary")
    description = models.TextField(blank=True, verbose_name="Description")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")

    def __unicode__(self):
        return self.summary

    class Meta:
        ordering = ['summary']
        unique_together = (('summary', 'couple'),)
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class CategoryWeight(models.Model):
    """
    This is the 'join table' or 'through table' for the many to many
    relationship between Homebuyer and Category, which contains an
    additional field for the individual homebuyer to weight the importance
    of the category.  Because the Category model has a foreign key to the
    Couple model rather than the Homebuyer, it is important to ensure
    the Couple instance is the same for both the homebuyer and category
    fields.
    """
    weight = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                          MaxValueValidator(100)],
                                              help_text="0-100",
                                              verbose_name="Weight")
    homebuyer = models.ForeignKey('core.Homebuyer', verbose_name="Homebuyer")
    category = models.ForeignKey('core.Category', verbose_name="Category")

    def __unicode__(self):
        return u"{homebuyer} gives {category} a weight of {weight}.".format(
                homebuyer=self.homebuyer,
                category=self.category,
                weight=weight)

    def clean(self, *args, **kwargs):
        if self.homebuyer.couple_id != self.category.couple_id:
            raise ValidationError("Category '{category}' is for a different "
                                  "Homebuyer.".format(category=self.category))
        super(CategoryWeight, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['category', 'homebuyer']
        unique_together = (('homebuyer', 'category'),)
        verbose_name = "Category Weight"
        verbose_name_plural = "Category Weights"


class Couple(models.Model):
    """
    Represents a couple in our app, or two prospective Homebuyers.  Operating
    under the assumption that a couple will have exactly one Realtor.
    This model is related to the Homebuyer model through a reverse foreign key;
    or put a different way, the Homebuyer model has a required foreign key to
    this Couple model.  What this means from a database perspective is that
    a Couple instance can have zero to infinity Homebuyer instances connected
    to it, so it is up to the app to ensure this is limited to 1 or 2 (the
    case where a Couple only has 1 Homebuyer is when one account has been
    activated but not the other).
    """
    realtor = models.ForeignKey('core.Realtor', verbose_name="Realtor")

    def __unicode__(self):
        username = 'user__username'
        homebuyers = (self.homebuyer_set
                      .values_list(username, flat=True).order_by(username))
        if not homebuyers:
            homebuyers = ['?', '?']
        elif homebuyers.count() == 1:
            homebuyers = [homebuyers.first(), '?']
        return u" and ".join(homebuyers)

    class Meta:
        ordering = ['realtor']
        verbose_name = "Couple"
        verbose_name_plural = "Couples"


class Grade(models.Model):
    """
    Each homebuyer will be related to several House and Category instances via
    a Couple instance.  This model will represent a homebuyer's grade for a
    specific house/category combination.
    """
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

    def clean(self):
        """
        The House, Category, and Homebuyer models all have a ForeignKey to a
        Couple instance, so make sure these are all consistent.
        """
        if (self.house.couple_id != self.category.couple_id or
                self.category.couple_id != self.homebuyer.couple_id):
            raise ValidationError("House, Category, and Homebuyer must all be "
                                  "for the same Couple.")
        super(Grade, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['homebuyer', 'house', 'category', 'score']
        unique_together = (('house', 'category', 'homebuyer'),)
        verbose_name = "Grade"
        verbose_name_plural = "Grades"


class Homebuyer(Person):
    """
    Represents an individual homebuyer.  The Homebuyer instance must be part
    of a couple, but the partner field may be blank if their partner has
    not yet registered.
    """
    partner = models.OneToOneField('core.Homebuyer', blank=True, null=True,
                                   verbose_name="Partner")
    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category', through='core.CategoryWeight',
                                        verbose_name="Categories")

    def clean(self):
        """
        Ensure that all related categories are for the correct Couple.
        """
        # TODO
        super(Homebuyer, self).clean(*args, **kwargs)

    class Meta:
        ordering = ['user__username']
        verbose_name = "Homebuyer"
        verbose_name_plural = "Homebuyers"


class House(models.Model):
    """
    Represents a single house in the database for a particular couple.
    Different couples might have the same house in their list of options, but
    these will be separate database objects because they might have nicknamed
    them differently.
    """
    nickname = models.CharField(max_length=128, verbose_name="Nickname")
    address = models.TextField(blank=True, verbose_name="Address")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category', through='core.Grade',
                                        verbose_name="Categories")

    def clean(self):
        """
        Ensure that all related categories are for the correct Couple.
        """
        # TODO
        super(Homebuyer, self).clean(*args, **kwargs)

    def __unicode__(self):
        return self.nickname

    class Meta:
        ordering = ['nickname']
        unique_together = (('nickname', 'couple'),)
        verbose_name = "House"
        verbose_name_plural = "Houses"


class Realtor(Person):
    class Meta:
        ordering = ['user__username']
        verbose_name = "Realtor"
        verbose_name_plural = "Realtors"
