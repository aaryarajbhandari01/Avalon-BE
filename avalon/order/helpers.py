from .models import Coupon


def check_coupon(code):
    try:
        coupon = Coupon.objects.get(code=code)
        if coupon.is_active:
            return coupon
        else:
            return None
    except Coupon.DoesNotExist:
        return None
