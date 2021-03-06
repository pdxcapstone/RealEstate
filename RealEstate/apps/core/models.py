import itertools

from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import IntegrityError, models, transaction
from django.dispatch import receiver
from django.utils.crypto import get_random_string, hashlib

__all__ = ['BaseModel', 'Category', 'CategoryWeight', 'Couple', 'Grade',
           'Homebuyer', 'House', 'Realtor', 'User']


_CATEGORIES = {
    'condition': {
        'summary': 'Condition',
        'description': 'Rate the overall condition of the house',
    },
    'location': {
        'summary': 'Location',
        'description': ('Rate the neighborhood, walkability, commute, and '
                        'nearby attractions')
    },
    'mortgage': {
        'summary': 'Mortgage',
        'description': ('Rate the mortgage based on price alone, not relative '
                        'to other rating categories')
    },
    'schools': {
        'summary': 'Schools',
        'description': 'Quality of school district'
    },
    'mastersuite': {
        'summary': 'Master Suite',
        'description': 'Condition of main bedroom and ensuite'
    },
    'kitchen': {
        'summary': 'Kitchen',
        'description': 'How nice the space is where food happens'
    },
    'naturallight': {
        'summary': 'Natural Light',
        'description': 'How bright and light it is during the day'
    },
    'gardening': {
        'summary': 'Gardening',
        'description': ('Potential to grow fruits, plants, vegetables, '
                        'and flowers')
    },
    'greatroom': {
        'summary': 'Great Room',
        'description': ('Presence and quality of a space to gather '
                        'and relax socially')
    },
    'privacy': {
        'summary': 'Privacy',
        'description': 'Proximity and shielding from neighbors'
    },
    'outdoorplayspace': {
        'summary': 'Outdoor Playspace',
        'description': 'Ability to relax and play outside'
    },
    'laundry': {
        'summary': 'Laundry',
        'description': 'Located conveniently, in a sensible space'
    },
    'noise': {
        'summary': 'Noise',
        'description': 'Noise levels throughout the day'
    }
    # ....
}

_DEFAULT_CATEGORIES = [
    _CATEGORIES['condition'],
    _CATEGORIES['location'],
    _CATEGORIES['mortgage']
]


@receiver(models.signals.post_save)
def _add_default_categories(sender, instance, created, **kwargs):
    """
    Add default categories for a couple when the first Homebuyer registers.
    """
    if created and sender == Couple:
        couple = instance
        categories = [Category(couple_id=couple.id, **category_data)
                      for category_data in _DEFAULT_CATEGORIES]
        with transaction.atomic():
            created_categories = Category.objects.bulk_create(categories)
            homebuyers = couple.homebuyer_set.all()
            category_weights = [
                CategoryWeight(category=category, homebuyer=homebuyer)
                for category in created_categories
                for homebuyer in homebuyers]
            CategoryWeight.objects.bulk_create(category_weights)
    return


@receiver(models.signals.post_save)
def _add_default_weights_and_grades(sender, instance, created, **kwargs):
    """
    When a Homebuyer, Category, or House gets created/saved, make sure
    CategoryWeight/Grade instances exist for all Homebuyers and all
    Category/House combinations.
    """
    homebuyers = []
    if sender == Homebuyer:
        homebuyers = [instance]
    elif sender in [Category, House]:
        homebuyers = instance.couple.homebuyer_set.all()

    with transaction.atomic():
        for homebuyer in homebuyers:
            unweighted_categories = homebuyer.unweighted_categories()
            if unweighted_categories:
                category_weights = map(
                    lambda category: CategoryWeight(category=category,
                                                    homebuyer=homebuyer),
                    unweighted_categories)
                CategoryWeight.objects.bulk_create(category_weights)

            ungraded_house_categories = homebuyer.ungraded_house_categories()
            if ungraded_house_categories:
                def _grade_mapper(house_category):
                    house, category = house_category
                    return Grade(house=house, category=category,
                                 homebuyer=homebuyer)

                grades = map(_grade_mapper, ungraded_house_categories)
                Grade.objects.bulk_create(grades)
    return


def _generate_email_confirmation_token():
    while True:
        token = hashlib.sha256(
            get_random_string(length=64)).hexdigest()
        if not User.objects.filter(email_confirmation_token=token).exists():
            return token


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

        category_couple_ids = set(self.categories
                                  .values_list('couple', flat=True))
        if category_couple_ids:
            if (len(category_couple_ids) > 1 or
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

    def clean_fields(self, exclude=None):
        """
        Strip all leading/trailing whitespace from CharFields and TextFields.
        """
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                fieldname = field.name
                value = getattr(self, fieldname)
                if value:
                    setattr(self, fieldname, value.strip())
        return super(BaseModel, self).clean_fields(exclude=exclude)

    class Meta:
        abstract = True


class Person(BaseModel):
    """
    Abstract model class representing information that is common to both
    Homebuyer and Realtor.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name="User")

    def __unicode__(self):
        name = self.full_name or '?'
        return u"{name} <{email}>".format(name=name, email=self.email)

    def can_view_report_for_couple(self, couple_id):
        """
        Returns a boolean indicating whether or not the Person instance can
        view the report for a given Couple.  This behavior will differ for the
        different subclasses (Homebuyer/Realtor), so the implementations
        should be defined there.
        """
        raise NotImplementedError

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        return self.user.get_full_name()

    class Meta:
        abstract = True


class Category(BaseModel):
    """
    Represents a category for a single couple, meaning each couple will define
    their own categories that are important to them rather than every couple
    sharing from the same list.
    """
    _SUMMARY_MIN_LENGTH = 1

    summary = models.CharField(max_length=128, verbose_name="Category Name")
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
    weight = models.PositiveSmallIntegerField(
        choices=((1, 'Unimportant'),
                 (2, 'Below Average'),
                 (3, 'Average'),
                 (4, 'Above Average'),
                 (5, 'Important')),
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Weight")
    homebuyer = models.ForeignKey('core.Homebuyer', verbose_name="Homebuyer")
    category = models.ForeignKey('core.Category', verbose_name="Category")

    def __unicode__(self):
        return u"{homebuyer} gives {category} a weight of {weight}".format(
            homebuyer=self.homebuyer,
            category=self.category,
            weight=self.weight)

    def clean(self):
        """
        Ensure the homebuyer is weighting a category that is actually linked
        with them.
        """
        foreign_key_ids = (self.homebuyer_id, self.category_id)
        if not all(foreign_key_ids):
            raise ValidationError("Homebuyer and Category must exist before "
                                  "saving a CategoryWeight instance.")

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
        return u", ".join(
            (unicode(hb) if hb else '?' for hb in self._homebuyers()))

    def _homebuyers(self):
        homebuyers = self.homebuyer_set.order_by('id')
        if not homebuyers:
            homebuyers = (None, None)
        elif homebuyers.count() == 1:
            homebuyers = (homebuyers.first(), None)
        return homebuyers

    def emails(self):
        return ','.join(
            self.homebuyer_set.values_list('user__email', flat=True))

    @property
    def registered(self):
        return self.homebuyer_set.count() == 2

    @property
    def report_data(self):
        """
        Report data for all homebuyers for this Couple, keyed by email.
        """
        return {homebuyer.email: homebuyer.report_data
                for homebuyer in self.homebuyer_set.all()}

    def report_url(self):
        if not self.id:
            return None
        return reverse('report', kwargs={'couple_id': self.id})

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
        choices=((1, 'Poor'),
                 (2, 'Below Average'),
                 (3, 'Average'),
                 (4, 'Above Average'),
                 (5, 'Excellent')),
        default=3,
        verbose_name="Score")

    house = models.ForeignKey('core.House', verbose_name="House")
    category = models.ForeignKey('core.Category', verbose_name="Category")
    homebuyer = models.ForeignKey('core.Homebuyer', verbose_name="Homebuyer")

    def __unicode__(self):
        return (u"{homebuyer} gives {house} a score of {score} for category: "
                "'{category}'".format(homebuyer=self.homebuyer.full_name,
                                      house=unicode(self.house),
                                      score=self.score,
                                      category=unicode(self.category)))

    def clean(self):
        """
        The House, Category, and Homebuyer models all have a ForeignKey to a
        Couple instance, so make sure these are all consistent.
        """
        foreign_key_ids = (self.house_id, self.category_id, self.homebuyer_id)
        if not all(foreign_key_ids):
            raise ValidationError("House, Category, and Homebuyer must all "
                                  "exist before saving a Grade instance.")
        couple_ids = set([self.house.couple_id, self.category.couple_id,
                          self.homebuyer.couple_id])
        if len(couple_ids) > 1:
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
    of a couple, so this relationship is required.
    """
    couple = models.ForeignKey('core.Couple', verbose_name="Couple")
    categories = models.ManyToManyField('core.Category',
                                        through='core.CategoryWeight',
                                        verbose_name="Categories")

    def can_view_report_for_couple(self, couple_id):
        """
        Homebuyers can only see their own report.
        """
        return self.couple_id == couple_id

    @property
    def category_weight_total(self):
        """
        Sums up all the weight properties for each CategoryWeight object on the
        Homebuyer.
        """
        total = self.categoryweight_set.aggregate(models.Sum('weight'))
        return total.get('weight__sum') or 0

    def clean(self):
        """
        Homebuyers and Realtors are mutually exclusive.  User instances have
        reverse relationships to both models, so only one of those should
        exist.

        Additionally, ensure that all related categories are for the correct
        Couple, and the related Couple has no more than 2 homebuyers.
        """
        if hasattr(self.user, 'realtor'):
            raise ValidationError("{user} is already a Realtor, cannot also "
                                  "have a Homebuyer relation."
                                  .format(user=self.user))

        # No more than 2 homebuyers per couple.
        homebuyers = set(self.couple.homebuyer_set
                         .values_list('id', flat=True).distinct())
        homebuyers.add(self.id)
        if len(homebuyers) > 2:
            raise ValidationError("Couple already has 2 Homebuyers.")

        self._validate_categories_and_couples()
        return super(Homebuyer, self).clean()

    @property
    def partner(self):
        """
        Returns the partner Homebuyer instance for this particular Homebuyer,
        or None if their partner is not yet registered.  If the query returns
        more than one Homebuyer, something has gone wrong and there are more
        than two people in the Couple, and needs to be resolved.
        """
        related_homebuyers = self.couple.homebuyer_set.exclude(id=self.id)
        if related_homebuyers.count() > 1:
            raise IntegrityError("Couple has too many related Homebuyers and "
                                 "should be resolved immediately. "
                                 "(Couple ID: {id})".format(id=self.couple_id))
        return related_homebuyers.first()

    @property
    def report_data(self):
        """
        Dumps out the homebuyer statistics into a dictionary.  The top level is
        keyed by Category summaries, meaning an empty dict would be returned
        for a Homebuyer with no related Category instances.  For each Category,
        a weight property is given, along with a nested dict of Houses with
        corresponding grades for that Category/House.
        """
        category_weights = self.categoryweight_set.select_related('category')
        grades = self.grade_set.select_related('category', 'house')
        data = {
            category_weight.category.summary: {
                'weight': category_weight.weight,
                'houses': {}
            }
            for category_weight in category_weights
        }
        for grade in grades:
            summary = grade.category.summary
            house_nickname = grade.house.nickname
            data[summary]['houses'][house_nickname] = grade.score
        return data

    @property
    def home_report_data(self):
        """
        Dumps out the homebuyer statistics into a dictionary.  The top level is
        keyed by Category summaries, meaning an empty dict would be returned
        for a Homebuyer with no related Category instances.  For each Category,
        a weight property is given, along with a nested dict of Houses with
        corresponding grades for that Category/House.
        """
        category_weights = self.categoryweight_set.select_related('category')
        grades = self.grade_set.select_related('house', 'category')
        data = {
            grade.house.nickname:
            {
                'weight': 0,
                'categories': {}
            }
            for grade in grades
        }
        for grade in grades:
            summary = grade.category.summary
            house_nickname = grade.house.nickname
            for category_weight in category_weights:
                if category_weight.category.summary == summary:
                    data[house_nickname]['weight'] = category_weight.weight
            data[house_nickname]['categories'][summary] = grade.score

        return data

    def report_url(self):
        return self.couple.report_url()

    @property
    def role_type(self):
        return 'Homebuyer'

    def ungraded_house_categories(self):
        """
        Returns a list of (<House>, <Category>) tuples for which this Homebuyer
        has no corresponding Grade instance.
        """
        houses = self.couple.house_set.all()
        categories = self.couple.category_set.all()
        grades = self.grade_set.values_list('house_id', 'category_id')
        house_categories = itertools.product(houses, categories)

        def _ungraded_filter(house_category):
            house, category = house_category
            return (house.id, category.id) not in grades

        return filter(_ungraded_filter, house_categories)

    def unweighted_categories(self):
        """
        Returns a Category queryset for which the Homebuyer does not have a
        corresponding CategoryWeight.
        """
        return self.couple.category_set.exclude(categoryweight__homebuyer=self)

    class Meta:
        ordering = ['user__email']
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

    def address_lines(self):
        return map(lambda line: line.strip(), self.address.split('\n'))

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

    def evaluation_url(self):
        """
        Returns the URL to the evaluation page for a specific house.
        """
        return reverse('eval', kwargs={'house_id': self.id})

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
    def can_view_report_for_couple(self, couple_id):
        """
        Realtors can view all reports for their client Couples.
        """
        return self.couple_set.filter(id=couple_id).exists()

    def clean(self):
        """
        Homebuyers and Realtors are mutually exclusive.  User instances have
        reverse relationships to both models, so only one of those should
        exist.
        """
        if hasattr(self.user, 'homebuyer'):
            raise ValidationError("{user} is already a Homebuyer, cannot also "
                                  "have a Realtor relation."
                                  .format(user=self.user))
        return super(Realtor, self).clean()

    def get_couples_and_pending_couples(self):
        """
        Returns a 2-tuple where the first item is a queryset of Couple
        instances, and the second item is a queryset of PendingCouple instances
        for the realtor.  The Couple query is filtered to exclude those where
        only one of the homebuyers has registered.
        """
        pending_couples = self.pendingcouple_set.all()
        emails = pending_couples.values_list(
            'pendinghomebuyer__email', flat=True)
        couples = self.couple_set.exclude(homebuyer__user__email__in=emails)
        return (couples, pending_couples)

    @property
    def role_type(self):
        return 'Realtor'

    class Meta:
        ordering = ['user__email']
        verbose_name = "Realtor"
        verbose_name_plural = "Realtors"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, is_staff, is_superuser,
                     **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Email is a required field.")
        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model which uses email instead of a username for logging in.
    """
    _EMAIL_CONFIRMATION_MESSAGE = u"""
        Hello {name},

        Thank you for registering for {app_name}!
        Please login and then click the link below to complete registration:
            {email_confirmation_link}

    """
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
        error_messages={
            'unique': ("A user with this email already "
                       "exists.")
        })
    first_name = models.CharField(max_length=30, verbose_name="First Name")
    last_name = models.CharField(max_length=30, verbose_name="Last Name")
    phone = models.CharField(max_length=20, blank=True,
                             validators=[
                                 RegexValidator(
                                     regex="^[0-9-()+]{10,20}$",
                                     message=("Please enter a valid phone "
                                              "number."),
                                     code='phone_format'
                                 )
                             ],
                             verbose_name="Phone Number")
    is_staff = models.BooleanField(
        default=False,
        help_text=("Designates whether the user can log into this admin "
                   "site."),
        verbose_name="Staff Status")
    is_active = models.BooleanField(
        default=True,
        help_text=("Designates whether this user should be treated as "
                   "active. Unselect this instead of deleting accounts."),
        verbose_name="Active")
    email_confirmed = models.BooleanField(
        default=False,
        help_text=("Designates if this user has confirmed their email "
                   "address or not."),
        verbose_name="Email Confirmed")
    email_confirmation_token = models.CharField(
        max_length=64,
        default=_generate_email_confirmation_token,
        editable=False,
        unique=True,
        verbose_name="Email Confirmation Token")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # These are used to control which URLs are available to different types
    # of users.
    _ALL_TYPES_ALLOWED = set(['Homebuyer', 'Realtor'])
    _HOMEBUYER_ONLY = set(['Homebuyer'])
    _REALTOR_ONLY = set(['Realtor'])

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def clean(self):
        if hasattr(self, 'homebuyer') and hasattr(self, 'realtor'):
            raise ValidationError("User cannot be a Homebuyer and a Realtor.")
        return super(User, self).clean()

    def clean_fields(self, exclude=None):
        """
        Strip whitespace from first and last names.  Email is already
        normalized by a separate function.
        """
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        return super(User, self).clean_fields(exclude=exclude)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_full_name(self):
        return u"{first} {last}".format(first=self.first_name,
                                        last=self.last_name).strip()

    def get_short_name(self):
        return self.first_name

    @property
    def role_object(self):
        """
        Returns the object which represents the user type (Homebuyer or
        Realtor).  If they are registered as both, raise an IntegrityError.
        Returns None if registered as neither.
        """
        has_homebuyer = hasattr(self, 'homebuyer')
        has_realtor = hasattr(self, 'realtor')
        if has_homebuyer:
            if has_realtor:
                raise IntegrityError("User {user} is registered as both a "
                                     "Homebuyer and a Realtor, which is not "
                                     "valid.".format(user=unicode(self)))
            return self.homebuyer
        elif has_realtor:
            return self.realtor
        return None

    def send_email_confirmation(self, request):
        """
        Sends out the email confirmation link to a new user.  Does nothing if
        the email is already confirmed.
        """
        if self.email_confirmed:
            return True

        app_name = settings.APP_NAME
        subject = u"{app_name} Email Confirmation".format(app_name=app_name)
        email_kwargs = {
            'email_confirmation_token': self.email_confirmation_token
        }
        email_confirmation_link = (
            request.get_host() + reverse('confirm-email', kwargs=email_kwargs))
        message = self._EMAIL_CONFIRMATION_MESSAGE.format(
            name=self.get_short_name(),
            app_name=app_name,
            email_confirmation_link=email_confirmation_link)
        try:
            self.email_user(subject, message,
                            from_email=settings.EMAIL_HOST_USER)
        except:
            return False
        return True
