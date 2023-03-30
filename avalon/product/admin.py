from django.contrib import admin

from .models import (
    # Cart,
    Category,
    Color,
    Product,
    ProductImages,
    ProductReview,
    Size,
    Wishlist,
)

admin.site.register(Product)
admin.site.register(ProductImages)
admin.site.register(ProductReview)
# admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(Category)
admin.site.register(Color)
admin.site.register(Size)
