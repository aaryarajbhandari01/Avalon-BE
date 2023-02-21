from django.urls import path

from .views import (CheckOutView, ConfirmKhaltiPaymentView, CouponCheckView,
                    OrderListView, PaymentView, ShippingDetailsCreateView,
                    ShippingDetailsDeleteView, ShippingDetailsListView,
                    ShippingDetailsUpdateView)

app_name = "order"

urlpatterns = [
    path("checkout/", CheckOutView.as_view(), name="checkout"),
    path("coupon-check/", CouponCheckView.as_view(), name="coupon_check"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("payment/", PaymentView.as_view(), name="payment"),
    path(
        "shipping-details/",
        ShippingDetailsListView.as_view(),
        name="shipping_details_list",
    ),
    path(
        "shipping-details/create/",
        ShippingDetailsCreateView.as_view(),
        name="shipping_details_create",
    ),
    path(
        "shipping-details/<int:pk>/update/",
        ShippingDetailsUpdateView.as_view(),
        name="shipping_details_update",
    ),
    path(
        "shipping-details/<int:pk>/delete/",
        ShippingDetailsDeleteView.as_view(),
        name="shipping_details_delete",
    ),
    path("khalti-payment/", ConfirmKhaltiPaymentView.as_view(), name="khalti_payment"),
]
