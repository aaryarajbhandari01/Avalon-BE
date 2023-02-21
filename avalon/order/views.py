from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, UpdateAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import Cart

from .khalti import initiate_payment
from .models import Coupon, Order, OrderItem, Payment, ShippingDetails
from .serializers import (CheckoutInputSerializer, CouponSerializer,
                          OrderSerializer, PaymentSerializer,
                          ShippingDetailsSerializer,
                          ShippingDetailsUpdateSerializer)

# ---------------------------------------------
# Shipping Details Views
# ---------------------------------------------


class ShippingDetailsCreateView(CreateAPIView):
    serializer_class = ShippingDetailsSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(
                {"message": "Shipping details created"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShippingDetailsListView(ListAPIView):
    serializer_class = ShippingDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShippingDetails.objects.filter(user=self.request.user)


class ShippingDetailsUpdateView(UpdateAPIView):
    serializer_class = ShippingDetailsUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShippingDetails.objects.filter(user=self.request.user)


class ShippingDetailsDeleteView(DestroyAPIView):
    serializer_class = ShippingDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShippingDetails.objects.filter(user=self.request.user)

    def delete(self, request, pk):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"message": "Shipping details deleted"}, status=status.HTTP_200_OK
        )


# ---------------------------------------------
# Order Views
# ---------------------------------------------


class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        filters = {}
        for key, value in self.request.query_params.items():
            filters[key] = value
        return Order.objects.filter(user=self.request.user, **filters)


class CouponCheckView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CouponSerializer

    def post(self, request):
        code = request.data["code"]
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_active:
                serializer = self.serializer_class(coupon)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"message": "Coupon is not active"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Coupon.DoesNotExist:
            return Response(
                {"message": "Coupon is invalid"}, status=status.HTTP_400_BAD_REQUEST
            )


class CheckOutView(APIView):
    checkout_serializer_class = CheckoutInputSerializer
    output_serializer_class = OrderSerializer

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        input_serializer = self.checkout_serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        cart_items = Cart.objects.filter(
            user=request.user, id__in=input_serializer.validated_data["cart_items"]
        ).prefetch_related("product")

        try:
            shipping_details = ShippingDetails.objects.get(
                id=input_serializer.validated_data["shipping_id"], user=request.user
            )
            coupon = Coupon.objects.get(
                code=input_serializer.validated_data["coupon_code"]
            )
            if not coupon.is_active:
                raise ValidationError(detail="Coupon code invalid.")
        except [ShippingDetails.DoesNotExist, Coupon.DoesNotExist]:
            raise ValidationError(detail="Shipping details or coupon not found.")

        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        discount_amount = (total_amount * coupon.discount_percent) / 100
        final_amount = total_amount - discount_amount

        order = Order(
            user=request.user,
            shipping_details=shipping_details,
            coupon=coupon,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
        )
        order.save()

        order_items = []
        for item in cart_items:
            if item.quantity > item.product.quantity:
                raise ValidationError(
                    detail=f"Product {item.product.name} out of stock."
                )
            item.product.quantity = item.product.quantity - item.quantity
            item.product.save()
            order_items.append(
                OrderItem(order=order, product=item.product, quantity=item.quantity)
            )

        OrderItem.objects.bulk_create(order_items)
        Payment.objects.create(order=order, amount=final_amount, user=request.user)

        cart_items.delete()

        output_serializer = self.output_serializer_class(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------
# Payment Views
# ---------------------------------------------


class PaymentView(APIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        payment_id = request.data["payment_id"]
        payment_method = request.data["payment_method"]
        payment = (
            Payment.objects.select_related("order")
            .filter(id=payment_id, user=request.user)
            .first()
        )
        if not payment:
            return Response(
                {"message": "Payment not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order = payment.order
        if payment_method == "KHALTI":
            payment.payment_method = "KHALTI"
            response = initiate_payment(amount=payment.amount, purchase_order_id=order.id, purchase_order_name=f"Order {order.id}")
            if "pidx" in response:
                payment.pidx = response["pidx"]
                payment.save()
                return Response(response, status=status.HTTP_200_OK)

        elif payment_method == "COD":
            payment.payment_method = "COD"
            payment.save()

            payment.order.status = "CONFIRMED"
            payment.order.save()

        serializer = self.serializer_class(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ConfirmKhaltiPaymentView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def get(self, request):
        pidx = request.query_params.get("pidx")

        payment = Payment.objects.select_related("order").filter(pidx=pidx).first()
        if not payment:
            return Response({"message": "Payment unsuccessful. Invalid PIDX"}, status=status.HTTP_400_BAD_REQUEST)
        
        payment.confirmed = True
        payment.save()

        order = payment.order
        order.order_status = "CONFIRMED"
        order.save()

        return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)
