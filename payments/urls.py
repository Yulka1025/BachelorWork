from django.urls import path
from .views import liqpay_callback

urlpatterns = [
    path("liqpay-callback/", liqpay_callback, name="liqpay_callback"),
]
