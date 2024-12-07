from django.contrib import admin
from .models import User, Product, Recommendation, Purchase, UserProduct, Unit, PurchaseCounter, Reminder

admin.site.register(User)
admin.site.register(Unit)
admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(Recommendation)
admin.site.register(UserProduct)
admin.site.register(PurchaseCounter)
admin.site.register(Reminder)
