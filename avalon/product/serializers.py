from rest_framework import serializers

from account.models import User

from .models import Cart, Category, Color, Product, ProductImages, ProductReview, Size


class ProductReviewUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ProductReviewSerializer(serializers.ModelSerializer):
    user = ProductReviewUserSerializer()

    class Meta:
        model = ProductReview
        fields = ["user", "product", "review"]


class ProductImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ["image"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["name"]


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ["name"]


class ProductSerializer(serializers.ModelSerializer):
    color = ColorSerializer(many=True, required=False)
    size = SizeSerializer(many=True, required=False)
    category = CategorySerializer(required=False)
    images = ProductImagesSerializer(many=True, read_only=True)
    product_review = ProductReviewSerializer(
        many=True, read_only=True, source="reviews"
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "product_review",
            "category",
            "color",
            "size",
            "price",
            "quantity",
            "banner",
            "isFeatured",
            "images",
        ]


class WishlistCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()


class WishlistDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class CartProductSerializer(serializers.ModelSerializer):
    images = ProductImagesSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "description", "images"]


class CartSerializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    total_price = serializers.SerializerMethodField()
    available = serializers.BooleanField(read_only=True, required=False)

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

    class Meta:
        model = Cart
        fields = ["id", "product", "quantity", "total_price", "available"]
