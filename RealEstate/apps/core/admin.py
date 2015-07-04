"""
Admin customization for core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor,
                                         User)
from RealEstate.apps.core.forms import UserCreationForm

admin.site.site_header = "Real Estate Admin"


# Inlines
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class CategoryWeightInline(admin.TabularInline):
    model = CategoryWeight
    extra = 0


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    fields = ('homebuyer', 'category', 'score')
    radio_fields = {'score': admin.HORIZONTAL}


class HomebuyerInline(admin.StackedInline):
    model = Homebuyer
    extra = 0
    max_num = 2


class HouseInline(admin.TabularInline):
    model = House
    extra = 0


# Custom Model Admins
class BaseAdmin(admin.ModelAdmin):
    """
    Admin settings for all models.
    """
    _READONLY_FIELDS_AFTER_CREATION = ('couple', 'user')
    save_on_top = True

    def get_readonly_fields(self, request, obj=None):
        """
        Make sure the fields defined in _READONLY_FIELDS_AFTER_CREATION are not
        edited after creating the object, which could cause weird side effects.
        """
        readonly_fields = super(BaseAdmin, self).get_readonly_fields(request,
                                                                     obj=obj)
        if obj:
            readonly_fields = list(readonly_fields)
            fieldnames_for_object = map(lambda f: f.name, obj._meta.fields)
            for fieldname in self._READONLY_FIELDS_AFTER_CREATION:
                if fieldname in fieldnames_for_object:
                    readonly_fields.append(fieldname)
        return readonly_fields

    def get_inline_instances(self, request, obj=None):
        """
        Only show inlines if the object exists in the database first.
        This is a precaution to help prevent the database from being
        in an invalid state as a result of the unusual schema.
        """
        if not obj:
            return []
        return super(BaseAdmin, self).get_inline_instances(request, obj=obj)


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
    fields = ('user', 'couple')
    inlines = [CategoryWeightInline]
    list_display = ('__unicode__', 'email', 'full_name')


@admin.register(House)
class HouseAdmin(BaseAdmin):
    inlines = [GradeInline]
    list_display = ('nickname', 'address')


@admin.register(Realtor)
class RealtorAdmin(BaseAdmin):
    list_display = ('__unicode__', 'email', 'full_name')


@admin.register(User)
class UserAdmin(UserAdmin):
    """
    Mostly copied from django.contrib.auth.admin.UserAdmin, but overridden to
    support email login.
    """
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login',)
    save_on_top = True

    add_form = UserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'phone', 'is_staff',
                    'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',
                   'last_login')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
