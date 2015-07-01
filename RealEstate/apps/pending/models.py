"""
Model definitions for pending couples and homebuyers, people who have been
invited to the app but have not yet registered.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.crypto import get_random_string, hashlib

from RealEstate.apps.core.models import BaseModel, Realtor


def _generate_registration_token():
    """
    Generate a random string, then generate a 64 character hex string using
    SHA-256.
    """
    while True:
        token = hashlib.sha256(get_random_string()).hexdigest()
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
        pending_homebuyers.discard(self.id)
        if len(pending_homebuyers) > 1:
            raise ValidationError("PendingCouple already has 2 Homebuyers.")
        return super(PendingHomebuyer, self).clean()

    @property
    def registration_status(self):
        """
        Returns a string representing the registration status of the pending
        homebuyer.  The homebuyer is considered registered if the email exists
        in the User table.
        """
        if User.objects.filter(email=self.email).exists():
            return u"Registered"
        return u"Unregistered"

    class Meta:
        ordering = ['email']
        verbose_name = "Pending Homebuyer"
        verbose_name_plural = "Pending Homebuyers"
