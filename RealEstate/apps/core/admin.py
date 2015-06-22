from django.contrib import admin

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor)

admin.site.register(Category)
admin.site.register(CategoryWeight)
admin.site.register(Couple)
admin.site.register(Grade)
admin.site.register(Homebuyer)
admin.site.register(House)
admin.site.register(Realtor)
