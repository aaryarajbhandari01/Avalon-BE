from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, UpdateAPIView)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from product.models import Cart, Product

from .khalti import initiate_payment
from .models import Coupon, Order, OrderItem, Payment, ShippingDetails
from .serializers import (CheckoutInputSerializer, CouponSerializer,
                          OrderSerializer, PaymentSerializer,
                          ShippingDetailsSerializer,
                          ShippingDetailsUpdateSerializer)

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Order, OrderItem, Coupon, Payment, ShippingDetails
from .serializers import (
    CheckoutInputSerializer,
    CouponSerializer,
    OrderSerializer,
    PaymentInputSerializer,
)


@api_view(["POST"])
def placeOrder(request):
    serializer = CheckoutInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Retrieve the shipping details
    shipping_details = ShippingDetails.objects.get(id=serializer.validated_data["shipping_id"])

    # Retrieve the cart items
    cart_items = OrderItem.objects.filter(
        user=request.user, ordered=False, item_status="In Cart"
    ).order_by("-date_added")

    # Calculate the order total
    order_total = sum(item.product.price * item.quantity for item in cart_items)

    # Apply the coupon code, if any
    coupon_code = serializer.validated_data.get("coupon_code")
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            discount = coupon.discount_percent / 100
            order_total -= order_total * discount
        except Coupon.DoesNotExist:
            pass

    # Create the order
    order = Order.objects.create(
        user=request.user,
        total_amount=order_total,
        shipping_details=shipping_details,
    )

    # Create the order items
    for item in cart_items:
        item.ordered = True
        item.save()
        order_item = OrderItem.objects.create(
            order=order, product=item.product, quantity=item.quantity
        )
        order.order_items.add(order_item)

    # Create the payment
    payment = Payment.objects.create(
        user=request.user, order=order, amount=order_total
    )

    # Return the serialized order
    order_serializer = OrderSerializer(order)
    return Response(order_serializer.data)
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


# class CheckOutView(APIView):
#     checkout_serializer_class = CheckoutInputSerializer
#     output_serializer_class = OrderSerializer

#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request):
#         input_serializer = self.checkout_serializer_class(data=request.data)
#         input_serializer.is_valid(raise_exception=True)

#         cart_items = Cart.objects.filter(
#             user=request.user, id__in=input_serializer.validated_data["cart_items"]
#         ).prefetch_related("product")

#         try:
#             shipping_details = ShippingDetails.objects.get(
#                 id=input_serializer.validated_data["shipping_id"], user=request.user
#             )
#             coupon = Coupon.objects.get(
#                 code=input_serializer.validated_data["coupon_code"]
#             )
#             if not coupon.is_active:
#                 raise ValidationError(detail="Coupon code invalid.")
#         except [ShippingDetails.DoesNotExist, Coupon.DoesNotExist]:
#             raise ValidationError(detail="Shipping details or coupon not found.")

#         total_amount = sum(item.product.price * item.quantity for item in cart_items)
#         discount_amount = (total_amount * coupon.discount_percent) / 100
#         final_amount = total_amount - discount_amount

#         order = Order(
#             user=request.user,
#             shipping_details=shipping_details,
#             coupon=coupon,
#             total_amount=total_amount,
#             discount_amount=discount_amount,
#             final_amount=final_amount,
#         )
#         order.save()

#         order_items = []
#         for item in cart_items:
#             if item.quantity > item.product.quantity:
#                 raise ValidationError(
#                     detail=f"Product {item.product.name} out of stock."
#                 )
#             item.product.quantity = item.product.quantity - item.quantity
#             item.product.save()
#             order_items.append(
#                 OrderItem(order=order, product=item.product, quantity=item.quantity)
#             )

#         OrderItem.objects.bulk_create(order_items)
#         Payment.objects.create(order=order, amount=final_amount, user=request.user)

#         cart_items.delete()

#         output_serializer = self.output_serializer_class(order)
#         return Response(output_serializer.data, status=status.HTTP_201_CREATED)

# class CheckOutView(APIView):
#     checkout_serializer_class = CheckoutInputSerializer
#     output_serializer_class = OrderSerializer

#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request):
#         input_serializer = self.checkout_serializer_class(data=request.data)
#         input_serializer.is_valid(raise_exception=True)

#         cart_items = input_serializer.validated_data["cart_items"]
#         product_ids = [item["product"] for item in cart_items]

#         # Fetch products and ensure they exist
#         products = Product.objects.filter(id__in=product_ids)
#         if len(products) != len(product_ids):
#             raise ValidationError(detail="One or more products not found.")

#         # Create order
#         try:
#             shipping_details = ShippingDetails.objects.get(
#                 id=input_serializer.validated_data["shipping_id"], user=request.user
#             )
#             coupon = Coupon.objects.get(
#                 code=input_serializer.validated_data["coupon_code"]
#             )
#             if not coupon.is_active:
#                 raise ValidationError(detail="Coupon code invalid.")
#         except [ShippingDetails.DoesNotExist, Coupon.DoesNotExist]:
#             raise ValidationError(detail="Shipping details or coupon not found.")

#         total_amount = sum(float(item["price"]) * item["quantity"] for item in cart_items)
#         discount_amount = (total_amount * coupon.discount_percent) / 100
#         final_amount = total_amount - discount_amount

#         order = Order(
#             user=request.user,
#             shipping_details=shipping_details,
#             coupon=coupon,
#             total_amount=total_amount,
#             discount_amount=discount_amount,
#             final_amount=final_amount,
#         )
#         order.save()

#         order_items = []
#         for item in cart_items:
#             product = next((p for p in products if str(p.id) == str(item["product"])), None)
#             if product is None:
#                 raise ValidationError(detail=f"Product {item['product']} not found.")
#             if item["quantity"] > product.quantity:
#                 raise ValidationError(
#                     detail=f"Product {product.name} out of stock."
#                 )

        
#             product.quantity = product.quantity - item["quantity"]
#             product.save()
#             order_items.append(
#                 OrderItem(order=order, product=product, quantity=item["quantity"])
#             )

#         OrderItem.objects.bulk_create(order_items)
#         Payment.objects.create(order=order, amount=final_amount, user=request.user)

#         output_serializer = self.output_serializer_class(order)
#         return Response(output_serializer.data, status=status.HTTP_201_CREATED)

import re

class CheckOutView(APIView):
    checkout_serializer_class = CheckoutInputSerializer
    output_serializer_class = OrderSerializer

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        input_serializer = self.checkout_serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        cart_items = input_serializer.validated_data["cart_items"]
        product_ids = [re.search(r'\d+', item["product"]).group(0) for item in cart_items]

        # Fetch products and ensure they exist
        products = Product.objects.filter(id__in=product_ids)
        if len(products) != len(product_ids):
            raise ValidationError(detail="One or more products not found.")

       
       
        try:
            shipping_details = ShippingDetails.objects.filter(
                phone=input_serializer.validated_data["shipping_address"]["shipping_id"], user=request.user
            ).first()
        except ShippingDetails.DoesNotExist:
            shipping_details = None
        if shipping_details is None:
            raise ValidationError(detail="Invalid or missing shipping details.")

        try:
            coupon = Coupon.objects.get(
                code=input_serializer.validated_data["coupon_code"]
            )
            if not coupon.is_active:
                raise ValidationError(detail="Coupon code invalid.")
        except Coupon.DoesNotExist:
            raise ValidationError(detail="Coupon not found.")

        


        # total_amount = sum(float(item["price"]) * item["quantity"] for item in cart_items)
        # discount_amount = (total_amount * coupon.discount_percent) / 100
        # final_amount = total_amount - discount_amount

        total_amount = input_serializer.validated_data["total_amount"]
        discount_amount = input_serializer.validated_data["discount_amount"]
        final_amount = input_serializer.validated_data["total_amount"]
        # final_amount = input_serializer.validated_data["final_amount"]
        
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
            product = next((p for p in products if str(p.id) == str(re.search(r'\d+', item["product"]).group(0))), None)
            if product is None:
                raise ValidationError(detail=f"Product {item['product']} not found.")
            # if item["quantity"] > product.quantity:
            #     raise ValidationError(
            #         detail=f"Product {product.name} out of stock."
            #     )

            # product.quantity = product.quantity - item["quantity"]
            # product.save()
            # order_items.append(
            #     OrderItem(order=order, product=product, quantity=item["quantity"])
            # )
            if int(item["quantity"]) > product.quantity:
                raise ValidationError(
                    detail=f"Product {product.name} out of stock."
                )
                
            product.quantity = product.quantity - int(item["quantity"])
            product.save()
            order_items.append(
                OrderItem(order=order, product=product, quantity=int(item["quantity"]))
            )

        OrderItem.objects.bulk_create(order_items)
        
        payment = Payment.objects.create(
            user=request.user,
            order=order,
            payment_method=input_serializer.validated_data['payment_method'],
            payment_id=input_serializer.validated_data.get('payment_id', ''),
            amount=order.final_amount,
        )
        payment.save()
        # Payment.objects.create(order=order, amount=final_amount, user=request.user)
        if payment.payment_method == 'KHALTI':
            payment.confirmed=True
            order.order_status = 'CONFIRMED'
            order.save()
            payment.save()



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
            # if "pidx" in response:
            #     payment.pidx = response["pidx"]
            #     payment.save()
            #     return Response(response, status=status.HTTP_200_OK)
            if "token" in response:
                payment.payment_id = response["token"]
                payment.save()
                return Response({"url": response["redirect_url"]}, status=status.HTTP_200_OK)

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
        # pidx = request.query_params.get("pidx")
        token = request.query_params.get("token")

        # payment = Payment.objects.select_related("order").filter(pidx=pidx).first()
        payment = Payment.objects.select_related("order").filter(payment_id=token).first()
        if not payment:
            return Response({"message": "Payment unsuccessful. Invalid PIDX"}, status=status.HTTP_400_BAD_REQUEST)
        
        payment.confirmed = True
        payment.save()

        order = payment.order
        order.order_status = "CONFIRMED"
        order.save()

        return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)
