from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Unit(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        formatted_date = self.purchase_date.strftime('%d.%m.%y %H:%M:%S')
        return f'{self.quantity} of {self.product.name} purchased by {self.user.username} on {formatted_date}'


class Recommendation(models.Model):
    product1 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations_as_product1')
    product2 = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations_as_product2')
    quantity = models.PositiveIntegerField(default=1)
    probability = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.product1} and {self.product2}'

    class Meta:
        unique_together = ('product1', 'product2')


class UserProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.quantity} of {self.product.name} are available to the {self.user.username}'


class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} {self.product.name}'


class PurchaseCounter(models.Model):
    total_purchases = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.total_purchases)
