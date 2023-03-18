from django.db.models import BooleanField, Case, F, Value, When
from rest_framework import filters, status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# from order.models import Order, OrderItem

from .filters import CategoryFilterBackend, SizeFilterBackend
from .models import Cart, Product, ProductReview, Wishlist
from .serializers import (
    CartSerializer,
    ProductReviewSerializer,
    ProductSerializer,
    WishlistCreateSerializer,
    WishlistDeleteSerializer,
)

# ---------------------------------------------
# Product Views
# ---------------------------------------------


class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    # filter_backends = [filters.OrderingFilter, SizeFilterBackend, CategoryFilterBackend]
    # ordering_fields = ["price"]
  

class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


class FeaturedProductListView(ListAPIView):
    queryset = Product.objects.filter(isFeatured=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


# ---------------------------------------------
# Wishlist Views
# ---------------------------------------------


class WishlistListView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(wishlist__user=self.request.user)


class WishlistCreateView(APIView):
    serializer_class = WishlistCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            product = Product.objects.get(id=serializer.data["product_id"])
            Wishlist.objects.get_or_create(user=request.user, product=product)
            return Response(
                {"message": "Product added to wishlist"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WishlistDeleteView(APIView):
    serializer_class = WishlistDeleteSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        Wishlist.objects.filter(user=request.user, id=pk).delete()
        return Response({"message": "Product removed from wishlist"})


# ---------------------------------------------
# Cart Views
# ---------------------------------------------


class AddToCartView(CreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("id")
        quantity = request.data.get("quantity")
        product = Product.objects.get(id=product_id)
        cart = Cart.objects.get_or_create(user=request.user, product=product)[0]
        if product.quantity >= int(quantity):
            cart.quantity = int(quantity)
        else:
            return Response(
                {"message": "Not enough stock to add."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart.save()
        serializer = self.serializer_class(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request):
        cart_id = request.data.get("id")
        quantity = request.data.get("quantity")
        cart = Cart.objects.get(user=request.user, id=cart_id).select_related("product")
        product = cart.product
        if product.quantity >= int(quantity):
            cart.quantity = int(quantity)
        else:
            return Response(
                {"message": "Not enough stock to add."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart.save()
        serializer = self.serializer_class(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartListView(ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Cart.objects.select_related("product")
            .filter(user=self.request.user)
            .annotate(
                total_price=F("quantity") * F("product__price"),
                available=Case(
                    When(product__quantity__gte=F("quantity"), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        )


class CartDeleteView(APIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart_id = request.data.get("id")
        Cart.objects.filter(user=request.user, id=cart_id).delete()
        return Response({"message": "Product removed from cart"})


# ---------------------------------------------
# Product Review Views
# ---------------------------------------------


class ReviewCreateView(APIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        review = request.data.get("review")
        product = Product.objects.get(id=request.data.get("product_id"))
        user = request.user

        # if Product.objects.filter(
        #     order_item__order__user=user,
        #     order_item__order__delivery_status="DELIVERED",
        #     id=product.id,
        # ).exists():
        review = ProductReview.objects.create(
                user=user, product=product, review=review
            )
        serializer = self.serializer_class(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(
        #     {"message": "You have not purchased this product."},
        #     status=status.HTTP_400_BAD_REQUEST,
        # )


class ReviewDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        review_id = request.data.get("id")
        review = ProductReview.objects.get(user=request.user, id=review_id)
        review.delete()
        return Response({"message": "Review deleted"}, status=status.HTTP_200_OK)
