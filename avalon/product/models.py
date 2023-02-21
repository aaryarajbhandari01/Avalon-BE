from django.conf import settings
from django.db import models

from avalon.abstract_models import TimestampAbstractModel


class Category(TimestampAbstractModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super().save(*args, **kwargs)


class Color(TimestampAbstractModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super().save(*args, **kwargs)


class Size(TimestampAbstractModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super().save(*args, **kwargs)


class Product(TimestampAbstractModel):
    name = models.CharField(max_length=50)
    price = models.IntegerField()
    description = models.TextField()
    quantity = models.IntegerField()
    isFeatured = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    on_sale = models.BooleanField(default=False)
    banner = models.ImageField(upload_to="product_banners", blank=True, null=True)
    color = models.ManyToManyField(Color)
    size = models.ManyToManyField(Size)

    def __str__(self):
        return self.name


class ProductImages(TimestampAbstractModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="product_images", blank=True, null=True)

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"


class ProductReview(TimestampAbstractModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.CASCADE
    )
    review = models.TextField()

    def __str__(self):
        return self.product.name

    class Meta:
        unique_together = ["user", "product"]


class Cart(TimestampAbstractModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.product.name


class Wishlist(TimestampAbstractModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="wishlist", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.name
