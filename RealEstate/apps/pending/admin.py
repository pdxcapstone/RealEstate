"""
Admin customization for pending couples/homebuyers.
"""
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from RealEstate.apps.core.admin import BaseAdmin
from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer


class PendingHomebuyerInline(admin.StackedInline):
    model = PendingHomebuyer
    extra = 1
    max_num = 2
    fields = ('email', 'registration_token', 'registration_status')
    readonly_fields = ('registration_status', 'registration_token')


@admin.register(PendingCouple)
class PendingCoupleAdmin(BaseAdmin):
    inlines = [PendingHomebuyerInline]
    list_display = ('__unicode__', 'couple_link', 'realtor_link')
    ordering = ('realtor',)

    def couple_link(self, obj):
        return self._change_link(obj.couple)
    couple_link.short_description = "Couple"

    def realtor_link(self, obj):
        return self._change_link(obj.realtor)
    realtor_link.short_description = "Realtor"
