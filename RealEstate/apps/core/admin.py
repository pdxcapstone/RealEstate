"""
Admin customization for core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor,
                                         User)
from RealEstate.apps.core.forms import UserChangeForm, UserCreationForm

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

    def _change_link(self, obj, display_text=None):
        """
        This method provides an easy mechanism to display a related object in
        the changelist admin view.
        """
        if not obj:
            return '?'
        fragments = [obj._meta.app_label, obj._meta.model_name, 'change']
        change_url = reverse("admin:{}".format('_'.join(fragments)),
                             args=(obj.id,))
        display_text = display_text or unicode(obj)
        return format_html("<a href={}>{}</a>", change_url, display_text)

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
    list_display = ('__unicode__', 'realtor_link', 'homebuyer_one',
                    'homebuyer_two')

    def _homebuyer_link(self, obj, first=True):
        try:
            homebuyer_one, homebuyer_two = obj._homebuyers()
        except ValueError:
            return "Too many Homebuyers for Couple."
        hb = homebuyer_one if first else homebuyer_two
        return self._change_link(hb)

    def homebuyer_one(self, obj):
        return self._homebuyer_link(obj)
    homebuyer_one.short_description = "First Homebuyer"

    def homebuyer_two(self, obj):
        return self._homebuyer_link(obj, first=False)
    homebuyer_two.short_description = "Second Homebuyer"

    def realtor_link(self, obj):
        return self._change_link(obj.realtor)
    realtor_link.short_description = "Realtor"


@admin.register(Homebuyer)
class HomebuyerAdmin(BaseAdmin):
    fields = ('user', 'couple')
    inlines = [CategoryWeightInline]
    list_display = ('__unicode__', 'user_link', 'partner_link', 'couple_link')

    def couple_link(self, obj):
        return self._change_link(obj.couple)
    couple_link.short_description = "Couple"

    def partner_link(self, obj):
        return self._change_link(obj.partner)
    partner_link.short_description = "Partner"

    def user_link(self, obj):
        return self._change_link(obj.user)
    user_link.short_description = "User"


@admin.register(House)
class HouseAdmin(BaseAdmin):
    inlines = [GradeInline]
    list_display = ('nickname', 'address')


@admin.register(Realtor)
class RealtorAdmin(BaseAdmin):
    list_display = ('__unicode__', 'user_link', 'phone')

    def phone(self, obj):
        return obj.user.phone
    phone.short_description = "Phone Number"

    def user_link(self, obj):
        return self._change_link(obj.user)
    user_link.short_description = "User"


@admin.register(User)
class UserAdmin(UserAdmin, BaseAdmin):
    """
    Mostly copied from django.contrib.auth.admin.UserAdmin, but overridden to
    support email login.
    """
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'email_confirmation_token',
                                    'email_confirmed', 'groups',
                                    'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'email_confirmation_token')
    save_on_top = True

    add_form = UserCreationForm
    form = UserChangeForm
    list_display = ('email', 'homebuyer_realtor_link', 'first_name',
                    'last_name', 'phone', 'email_confirmed', 'is_staff',
                    'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',
                   'last_login')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def homebuyer_realtor_link(self, obj):
        role = obj.role_object
        if role:
            return self._change_link(role, display_text=role.role_type)
        return '?'
    homebuyer_realtor_link.short_description = "Homebuyer/Realtor"
