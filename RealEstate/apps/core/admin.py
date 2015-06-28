from django.contrib import admin

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor)

admin.site.site_header = "Real Estate Admin"


# Inlines
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1


class CategoryWeightInline(admin.TabularInline):
    model = CategoryWeight
    extra = 1


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 1
    fields = ('homebuyer', 'category', 'score')
    radio_fields = {'score': admin.HORIZONTAL}


class HomebuyerInline(admin.StackedInline):
    model = Homebuyer
    extra = 1
    max_num = 2


class HouseInline(admin.TabularInline):
    model = House
    extra = 1


# Custom Model Admins
class BaseAdmin(admin.ModelAdmin):
    """
    Admin settings for all models.
    """
    save_on_top = True


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    fields = ('couple', 'summary', 'description')
    list_display = ('summary', 'couple')


@admin.register(Couple)
class CoupleAdmin(BaseAdmin):
    inlines = [HomebuyerInline, HouseInline, CategoryInline]
    list_display = ('__unicode__', 'realtor')


@admin.register(Homebuyer)
class HomebuyerAdmin(BaseAdmin):
    inlines = [CategoryWeightInline]
    list_display = ('__unicode__', 'email', 'full_name')


@admin.register(House)
class HouseAdmin(BaseAdmin):
    inlines = [GradeInline]
    list_display = ('nickname', 'address')


@admin.register(Realtor)
class RealtorAdmin(BaseAdmin):
    list_display = ('__unicode__', 'email', 'full_name')
