"""
Model definitions for pending couples and homebuyers, people who have been
invited to the app but have not yet registered.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError, models
from django.utils.crypto import get_random_string, hashlib

from RealEstate.apps.core.models import BaseModel, Couple, Homebuyer


def _generate_registration_token():
    """
    Generate a random string, then generate a 64 character hex string using
    SHA-256.
    """
    while True:
        token = hashlib.sha256(
            get_random_string(length=64)).hexdigest()
        if not PendingHomebuyer.objects.filter(registration_token=token):
            return token


class PendingCouple(BaseModel):
    """
    This model links the PendingHomebuyer instances with an existing realtor.
    """
    realtor = models.ForeignKey('core.Realtor', verbose_name="Realtor")

    def __unicode__(self):
        pending_homebuyers = self.pendinghomebuyer_set.all()
        if pending_homebuyers:
            return u", ".join(map(unicode, pending_homebuyers))
        return u"No homebuyers specified"

    @property
    def couple(self):
        """
        The real Couple instance for the two Homebuyers.  If neither have
        registered yet, it will not exist, but will be created after the first
        person registers.
        """
        emails = self.pendinghomebuyer_set.values_list('email', flat=True)
        homebuyers = Homebuyer.objects.filter(user__email__in=emails)
        couples = Couple.objects.filter(homebuyer__in=homebuyers)
        if couples.exists():
            return couples.first()
        return None

    def emails(self):
        return ','.join(
            self.pendinghomebuyer_set.values_list('email', flat=True))

    @property
    def registered(self):
        """
        Returns a boolean indicating whether or not all PendingHomebuyer
        instances related to this PendingCouple have been registered.
        """
        pending_homebuyers = self.pendinghomebuyer_set.all()
        return (pending_homebuyers.count() == 2 and
                all(map(lambda hb: hb.registered, pending_homebuyers)))

    class Meta:
        ordering = ['realtor']
        verbose_name = "Pending Couple"
        verbose_name_plural = "Pending Couples"


class PendingHomebuyer(BaseModel):
    """
    Represents a Homebuyer that has been invited but not yet registered in the
    database.
    """
    _HOMEBUYER_INVITE_MESSAGE = """
        Hello {name},

        You have been invited to {app_name}.
        Register at the following link:
            {signup_link}

    """

    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=30, verbose_name="First Name")
    last_name = models.CharField(max_length=30, verbose_name="Last Name")
    registration_token = models.CharField(max_length=64,
                                          default=_generate_registration_token,
                                          editable=False,
                                          unique=True,
                                          verbose_name="Registration Token")
    pending_couple = models.ForeignKey('pending.PendingCouple',
                                       verbose_name="Pending Couple")

    def __unicode__(self):
        return u"{first} {last} <{email}>".format(first=self.first_name,
                                                  last=self.last_name,
                                                  email=self.email)

    def _signup_link(self, host):
        """
        Construct the sign up link based on the host and registration_token
        for the PendingHomebuyer instance.
        """
        url = reverse('homebuyer-signup',
                      kwargs={'registration_token': self.registration_token})
        return host + url

    def clean(self):
        """
        Referenced pending_couple instance should be related to a maximum
        of two PendingHomebuyer instances.
        """
        if self.id:
            pending_homebuyers = set(self.pending_couple.pendinghomebuyer_set
                                     .values_list('id', flat=True).distinct())
            pending_homebuyers.add(self.id)
            if len(pending_homebuyers) > 2:
                raise ValidationError(
                    "PendingCouple already has 2 Homebuyers.")
        return super(PendingHomebuyer, self).clean()

    @property
    def couple(self):
        return self.pending_couple.couple

    @property
    def partner(self):
        """
        TODO: Same logic as Homebuyer.partner, needs refactor.
        """
        pending_homebuyers = (self.pending_couple
                              .pendinghomebuyer_set.exclude(id=self.id))
        if pending_homebuyers.count() > 1:
            raise IntegrityError("PendingCouple has too many related "
                                 "PendingHomebuyer and should be resolved "
                                 "immediately. (PendingCouple ID: {id})"
                                 .format(id=self.pending_couple.id))
        return pending_homebuyers.first()

    @property
    def registered(self):
        """
        Returns a boolean representing the registration status of the pending
        homebuyer.  The homebuyer is considered registered if the email exists
        in the User table.
        """
        return Homebuyer.objects.filter(user__email=self.email).exists()

    @property
    def registration_status(self):
        return "Registered" if self.registered else "Unregistered"

    def send_email_invite(self, request):
        """
        Sends out the email to the potential homebuyer, which includes a link
        to their custom signup page.  Does nothing if they are already
        registered.
        """
        if self.registered:
            return None

        app_name = settings.APP_NAME
        subject = u"{app_name} Invitation".format(app_name=app_name)
        message = self._HOMEBUYER_INVITE_MESSAGE.format(
            name=self.first_name,
            app_name=app_name,
            signup_link=self._signup_link(request.get_host()))
        return send_mail(subject, message, settings.EMAIL_HOST_USER,
                         [self.email], fail_silently=False)

    class Meta:
        ordering = ['email']
        verbose_name = "Pending Homebuyer"
        verbose_name_plural = "Pending Homebuyers"
