from django.contrib import admin

from .models import Coupon, Order, OrderItem, Payment, ShippingDetails

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(ShippingDetails)
admin.site.register(Coupon)
