from django.db import models
from django.contrib.auth.models import User

from catalog.models import Product


class Basket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="basket")

    def __str__(self):
        return f"Basket of {self.user.username}"


class BasketItem(models.Model):
    class Meta:
        unique_together = ("basket", "product")

    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="basket_items")
    count = models.PositiveIntegerField(default=1)


class DeliverySettings(models.Model):
    class Meta:
        verbose_name = "Delivery settings"
        verbose_name_plural = "Delivery settings"

    default_delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=3)
    free_delivery = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    express_delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=5)


class Order(models.Model):
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    DELIVERY_OPTIONS = [
        ("ordinary", "ordinary"),
        ("express", "express"),
    ]
    PAYMENT_OPTIONS = [
        ("online", "online"),
        ("someone", "someone"),
    ]
    STATUS_CHOICES = [
        ("created", "created"),
        ("accepted", "accepted"),
        ("paid", "paid"),
        ("failed", "failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_type = models.CharField(max_length=50, choices=DELIVERY_OPTIONS, default="ordinary")
    payment_type = models.CharField(max_length=50, choices=PAYMENT_OPTIONS, default="online")
    total_cost = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="created")
    city = models.CharField(max_length=100)
    address = models.TextField(max_length=255)
    products = models.ManyToManyField(Product, through="OrderItem", related_name="orders")
    payment_error = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    class Meta:
        unique_together = ("order", "product")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
