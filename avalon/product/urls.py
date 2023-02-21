from django.urls import path

from .views import (
    AddToCartView,
    CartDeleteView,
    CartListView,
    CartUpdateView,
    FeaturedProductListView,
    ProductDetailView,
    ProductListView,
    ReviewCreateView,
    ReviewDeleteView,
    WishlistCreateView,
    WishlistDeleteView,
    WishlistListView,
)

app_name = "product"

urlpatterns = [
    path("all/", ProductListView.as_view(), name="product_list"),
    path("featured/", FeaturedProductListView.as_view(), name="featured_product_list"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("wishlist/", WishlistListView.as_view(), name="wishlist_list"),
    path("wishlist/create/", WishlistCreateView.as_view(), name="wishlist_create"),
    path(
        "wishlist/<int:pk>/delete/",
        WishlistDeleteView.as_view(),
        name="wishlist_delete",
    ),
    path("add-to-cart/", AddToCartView.as_view(), name="add_to_cart"),
    path("cart/", CartListView.as_view(), name="cart_list"),
    path("cart/delete/", CartDeleteView.as_view(), name="cart_delete"),
    path("cart/update/", CartUpdateView.as_view(), name="cart_update"),
    path("review/create/", ReviewCreateView.as_view(), name="review_create"),
    path("review/delete/", ReviewDeleteView.as_view(), name="review_delete"),
]
