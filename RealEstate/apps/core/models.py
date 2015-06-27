from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

__all__ = ['Category', 'CategoryWeight', 'Couple', 'Grade', 'Homebuyer',
           'House', 'Realtor']


class ValidateCategoryCoupleMixin(object):
    """
    This is mixed in through multiple inheritance because the logic is common
    to indirectly related objects.
    """
    def _validate_categories_and_couples(self):
        """
        Homebuyer and House both have a foreign key to Couple, and a M2M with
        Category.  Since Category itself has a foreign key to Couple, these
        need to remain consistent.
        """
        if not self.pk:
            return

        category_couple_ids = (self.categories
                               .values_list('couple', flat=True).distinct())
        if category_couple_ids:
            if (category_couple_ids.count() > 1 or
                    self.couple_id not in category_couple_ids):
                raise ValidationError("Invalid categories for this couple.")
        return


class BaseModel(models.Model):
    """
    Abstract base model class for containing logic/fields we will want
    available in all of our models.
    """
    def _validate_min_length(self, fieldname, min_length):
        """
        Raises an error if the field length is less than the minimum provided.
        """
        field = getattr(self, fieldname, "")
        if not field or len(field) < min_length:
            raise ValidationError({
                fieldname: ["{fieldname} must be at least length {min_length}"
                            .format(fieldname=fieldname,
                                    min_length=min_length)]
            })
        return

    class Meta:
        abstract = True


class Person(BaseModel):
    """
    Abstract model class representing information that is common to both
    Homebuyer and Realtor.
    """
    user = models.OneToOneField('auth.User', verbose_name="User")

    def __unicode__(self):
        return self.user.username

    class Meta:
        abstract = True


class Category(BaseModel):
    """
    Represents a category for a single couple, meaning each couple will define
    their own categories that are important to them rather than every couple
    sharing from the same list.
    """
    _SUMMARY_MIN_LENGTH = 1

    summary = models.CharField(max_length=128, verbose_name="Summary")
    description = models.TextField(blank=True, verbose_name="Description")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")

    def __unicode__(self):
        return self.summary

    def clean_fields(self, exclude=None):
        """
        Make sure summary is not an empty string, which is what it would be
        saved in the database as by default.
        """
        self._validate_min_length('summary', self._SUMMARY_MIN_LENGTH)
        return super(Category, self).clean_fields(exclude=exclude)

    class Meta:
        ordering = ['summary']
        unique_together = (('summary', 'couple'),)
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class CategoryWeight(BaseModel):
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

    def clean(self):
        """
        Ensure the homebuyer is weighting a category that is actually linked
        with them.
        """
        if self.homebuyer.couple_id != self.category.couple_id:
            raise ValidationError("Category '{category}' is for a different "
                                  "Homebuyer.".format(category=self.category))
        return super(CategoryWeight, self).clean()

    class Meta:
        ordering = ['category', 'homebuyer']
        unique_together = (('homebuyer', 'category'),)
        verbose_name = "Category Weight"
        verbose_name_plural = "Category Weights"


class Couple(BaseModel):
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


class Grade(BaseModel):
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
        return super(Grade, self).clean()

    class Meta:
        ordering = ['homebuyer', 'house', 'category', 'score']
        unique_together = (('house', 'category', 'homebuyer'),)
        verbose_name = "Grade"
        verbose_name_plural = "Grades"


class Homebuyer(Person, ValidateCategoryCoupleMixin):
    """
    Represents an individual homebuyer.  The Homebuyer instance must be part
    of a couple, but the partner field may be blank if their partner has not
    yet registered.
    """
    partner = models.OneToOneField('core.Homebuyer', blank=True, null=True,
                                   verbose_name="Partner")
    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category',
                                        through='core.CategoryWeight',
                                        verbose_name="Categories")

    def clean(self):
        """
        Homebuyers and Realtors are mutually exclusive.  User instances have
        reverse relationships to both models, so only one of those should
        exist.

        Additionally, ensure that all related categories are for the correct
        Couple, and that the related Couple has no more than 2 homebuyers.
        """
        if hasattr(self.user, 'realtor'):
            raise ValidationError("{user} is already a Homebuyer, cannot also "
                                  "have a Realtor relation."
                                  .format(user=self.user))

        self._validate_categories_and_couples()

        # TODO: No more than 2 homebuyers per couple
        return super(Homebuyer, self).clean()

    class Meta:
        ordering = ['user__username']
        verbose_name = "Homebuyer"
        verbose_name_plural = "Homebuyers"


class House(BaseModel, ValidateCategoryCoupleMixin):
    """
    Represents a single house in the database for a particular couple.
    Different couples might have the same house in their list of options, but
    these will be separate database objects because they might have nicknamed
    them differently.
    """
    _NICKNAME_MIN_LENGTH = 1

    nickname = models.CharField(max_length=128, verbose_name="Nickname")
    address = models.TextField(blank=True, verbose_name="Address")

    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category', through='core.Grade',
                                        verbose_name="Categories")

    def __unicode__(self):
        return self.nickname

    def clean(self):
        """
        Ensure that all related categories are for the correct Couple.
        """
        self._validate_categories_and_couples()
        return super(House, self).clean()

    def clean_fields(self, exclude=None):
        """
        Make sure summary is not an empty string, which is what it would be
        saved in the database as by default.
        """
        self._validate_min_length('nickname', self._NICKNAME_MIN_LENGTH)
        return super(House, self).clean_fields(exclude=exclude)

    class Meta:
        ordering = ['nickname']
        unique_together = (('nickname', 'couple'),)
        verbose_name = "House"
        verbose_name_plural = "Houses"


class Realtor(Person):
    """
    Represents a realtor.  Each Couple instance has a required foreign key to
    Realtor, so each Realtor serves zero or more couples.
    """
    def clean(self):
        """
        Homebuyers and Realtors are mutually exclusive.  User instances have
        reverse relationships to both models, so only one of those should
        exist.
        """
        if hasattr(self.user, 'homebuyer'):
            raise ValidationError("{user} is already a Realtor, cannot also "
                                  "have a Homebuyer relation."
                                  .format(user=self.user))
        return super(Realtor, self).clean()

    class Meta:
        ordering = ['user__username']
        verbose_name = "Realtor"
        verbose_name_plural = "Realtors"
