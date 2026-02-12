from django.urls import path
from .views import BasketAPIView, OrdersAPIView, OrderDetailAPIView, PaymentAPIView


urlpatterns  = [
    path("basket", BasketAPIView.as_view(), name="basket"),
    path("orders", OrdersAPIView.as_view(), name="orders"),
    path("order/<int:order_id>", OrderDetailAPIView.as_view(), name="order_detail"),
    path("payment/<int:order_id>", PaymentAPIView.as_view(), name="payment"),
]
