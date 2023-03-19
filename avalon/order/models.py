from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from avalon.abstract_models import TimestampAbstractModel
from product.models import Product


class Coupon(TimestampAbstractModel):
    code = models.CharField(max_length=50)
    discount_percent = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], default=1
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        return super().save(*args, **kwargs)


class ShippingDetails(TimestampAbstractModel):
    PROVINCE_CHOICES = (
        ("P1", "Province 1"),
        ("MP", "Madhesh Pradesh"),
        ("BG", "Bagmati"),
        ("GK", "Gandaki"),
        ("LB", "Lumbini"),
        ("KR", "Karnali"),
        ("SP", "Sudurpashchim"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    # province = models.CharField(max_length=50, choices=PROVINCE_CHOICES)
    phone = models.CharField(max_length=10)#, primary_key=True

    def __str__(self):
        return f"{self.user.username} - {self.address} - {self.city} - {self.province} - {self.phone}"

    class Meta:
        verbose_name = "Shipping Detail"
        verbose_name_plural = "Shipping Details"


class Order(TimestampAbstractModel):
    ORDER_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
    ]
    DELIVERY_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("DELIVERED", "Delivered"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="order", on_delete=models.CASCADE
    )
    shipping_details = models.ForeignKey(
        ShippingDetails, related_name="order", on_delete=models.CASCADE
    )
    total_amount = models.IntegerField()
    discount_amount = models.IntegerField()
    final_amount = models.IntegerField()

    order_status = models.CharField(
        max_length=50, choices=ORDER_STATUS_CHOICES, default="PENDING"
    )
    delivery_status = models.CharField(
        max_length=50, choices=DELIVERY_STATUS_CHOICES, default="PENDING"
    )
    coupon = models.ForeignKey(
        Coupon, related_name="order", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.shipping_details} - {self.order_status}"


class Payment(TimestampAbstractModel):
    PAYMENT_METHOD_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("KHALTI", "Khalti"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="payment", on_delete=models.CASCADE
    )
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, max_length=50)
    payment_id = models.CharField(max_length=50, null=True, blank=True)
    order = models.ForeignKey(Order, related_name="payment", on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.order} - {self.amount}"


class OrderItem(TimestampAbstractModel):
    order = models.ForeignKey(
        Order, related_name="order_items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.CASCADE
    )
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.order} - {self.product} - {self.quantity}"

    def check_stock(self):
        return self.product.quantity >= self.quantity
