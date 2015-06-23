from django.contrib import admin

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor)


# Inlines
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1


class HomebuyerInline(admin.StackedInline):
    model = Homebuyer
    extra = 1
    max_num = 2


class HouseInline(admin.TabularInline):
    model = House
    extra = 1


# Custom Model Admins
class CategoryAdmin(admin.ModelAdmin):
    fields = ('couple', 'summary', 'description')
    list_display = ('summary', 'couple')


class CoupleAdmin(admin.ModelAdmin):
    inlines = [HomebuyerInline, HouseInline, CategoryInline]
    list_display = ('__unicode__', 'realtor')


admin.site.site_header = "Real Estate Admin"

admin.site.register(Category, CategoryAdmin)
admin.site.register(CategoryWeight)
admin.site.register(Couple, CoupleAdmin)
admin.site.register(Grade)
admin.site.register(Homebuyer)
admin.site.register(House)
admin.site.register(Realtor)
