"""
Admin customization for pending couples/homebuyers.
"""
from django.contrib import admin

from RealEstate.apps.core.admin import BaseAdmin
from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer


class PendingHomebuyerInline(admin.StackedInline):
    model = PendingHomebuyer
    extra = 1
    max_num = 2
    fields = ('email', 'first_name', 'last_name', 'registration_token',
              'registration_status')
    readonly_fields = ('registration_status', 'registration_token')


@admin.register(PendingCouple)
class PendingCoupleAdmin(BaseAdmin):
    inlines = [PendingHomebuyerInline]
