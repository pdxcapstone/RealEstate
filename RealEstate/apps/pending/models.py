"""
Model definitions for pending couples and homebuyers, people who have been
invited to the app but have not yet registered.
"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.utils.crypto import get_random_string, hashlib

from RealEstate.apps.core.models import BaseModel


def _generate_registration_token():
    """
    Generate a random string, then generate a 64 character hex string using
    SHA-256.
    """
    while True:
        token = hashlib.sha256(get_random_string(length=64)).hexdigest()
        if not PendingHomebuyer.objects.filter(registration_token=token):
            return token


class PendingCouple(BaseModel):
    """
    This model links the PendingHomebuyer instances with an existing realtor.
    """
    realtor = models.ForeignKey('core.Realtor', verbose_name="Realtor")

    def __unicode__(self):
        homebuyer_string = u"No homebuyers specified"
        pending_homebuyers = self.pendinghomebuyer_set.order_by('email')
        if pending_homebuyers:
            homebuyer_string = u", ".join(map(unicode, pending_homebuyers))
        return u"{realtor}: {homebuyer_string}".format(
            realtor=self.realtor,
            homebuyer_string=homebuyer_string)

    class Meta:
        ordering = ['realtor']
        verbose_name = "Pending Couple"
        verbose_name_plural = "Pending Couples"


class PendingHomebuyer(BaseModel):
    """
    Represents a Homebuyer that has been invited but not yet registered in the
    database.
    """
    email = models.EmailField(max_length=75, unique=True,
                              verbose_name="Email")
    registration_token = models.CharField(max_length=64,
                                          default=_generate_registration_token,
                                          editable=False,
                                          unique=True,
                                          verbose_name="Registration Token")
    pending_couple = models.ForeignKey('pending.PendingCouple',
                                       verbose_name="Pending Couple")

    def __unicode__(self):
        return u"{email} ({registration_status})".format(
            email=self.email,
            registration_status=self.registration_status)

    def clean(self):
        """
        Referenced pending_couple instance should be related to a maximum
        of two PendingHomebuyer instances.
        """
        pending_homebuyers = set(self.pending_couple.pendinghomebuyer_set
                                 .values_list('id', flat=True).distinct())
        pending_homebuyers.add(self.id)
        if len(pending_homebuyers) > 2:
            raise ValidationError("PendingCouple already has 2 Homebuyers.")
        return super(PendingHomebuyer, self).clean()

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
        if User.objects.filter(email=self.email).exists():
            return True
        return False

    @property
    def registration_status(self):
        return "Registered" if self.registered else "Unregistered"

    class Meta:
        ordering = ['email']
        verbose_name = "Pending Homebuyer"
        verbose_name_plural = "Pending Homebuyers"
