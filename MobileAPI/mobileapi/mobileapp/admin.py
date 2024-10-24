from django.contrib import admin
from .models import User, Product, Recommendation, Purchase, UserProduct

admin.site.register(User)
admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(Recommendation)
admin.site.register(UserProduct)
