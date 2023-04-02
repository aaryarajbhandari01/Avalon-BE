from rest_framework import serializers

from product.models import Product
from product.serializers import (ColorSerializer, ProductImagesSerializer,
                                 SizeSerializer)

from .models import Coupon, Order, OrderItem, Payment, ShippingDetails


class ShippingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingDetails
        fields = ["id", "address", "city", "province", "phone"]

    def validate(self, attrs):
        super().validate(attrs)
        if not len(attrs["phone"]) == 10:
            raise serializers.ValidationError("Invalid phone number")
        return attrs
    

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        extra_kwargs = {"amount": {"read_only": True},
                         "user": {"read_only": True}, 
                         "order": {"read_only": True}, 
                         "payment_id": {"required": False},#"read_only": True, 
                        "payment_method": { "required": False}} #"read_only": True



class ShippingDetailsUpdateSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    province = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, attrs):
        super().validate(attrs)
        if "phone" in self.initial_data and not len(attrs["phone"]) == 10:
            raise serializers.ValidationError("Invalid phone number")
        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class OrderItemProductSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True, read_only=True)
    size = SizeSerializer(many=True, read_only=True)
    color = ColorSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "color", "size", "images"]
        read_only_fields = ["id", "product", "quantity"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    shipping_details = ShippingDetailsSerializer(required=False)
    order_items = OrderItemSerializer(many=True, required=False)
    payment = PaymentSerializer(many=False) #, read_only=True

    class Meta:
        model = Order
        fields = [
            "id",
            "shipping_details",
            "order_items",
            "total_amount",
            "discount_amount",
            "final_amount",
            "order_status",
            "delivery_status",
            "payment",
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["id", "code", "discount_percent", "is_active"]


# class CheckoutInputSerializer(serializers.Serializer):
#     shipping_id = serializers.IntegerField()
#     coupon_code = serializers.CharField(required=False)
#     cart_items = serializers.ListField(child=serializers.IntegerField(), required=True)

class CheckoutInputSerializer(serializers.Serializer):
    # shipping_id = serializers.CharField(max_length=25)
    shipping_address = serializers.DictField(
        child=serializers.CharField(max_length=255), required=True
    )
    cart_items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(max_length=255), required=True
        ),
        required=True,
    )
    coupon_code = serializers.CharField(required=False)
    payment_method = serializers.ChoiceField(
        choices=["COD", "KHALTI"], required=True
    )
    shipping_price = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=True
    )
    total_amount = serializers.IntegerField()
    discount_amount = serializers.IntegerField()

class PaymentInputSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    amount = serializers.IntegerField()
