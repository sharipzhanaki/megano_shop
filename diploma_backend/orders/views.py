from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import BasketItem, Order
from .serializers import OrderSerializer, PaymentSerializer
from .services import BasketService, OrderService, PaymentService
from .utils import get_session_basket, get_or_create_user_basket
from catalog.models import Product
from catalog.serializers import ProductShortSerializer


class BasketAPIView(APIView):
    def get(self, request):
        items = []
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            for item in BasketItem.objects.filter(basket=basket).select_related("product"):
                data = ProductShortSerializer(item.product, context={"request": request}).data
                data["count"] = item.count
                items.append(data)
            return Response(items)
        for pid, count in get_session_basket(request).items():
            product = Product.objects.get(id=int(pid))
            data = ProductShortSerializer(product, context={"request": request}).data
            data["count"] = int(count)
            items.append(data)
        return Response(items)

    def post(self, request):
        pid = int(request.data["id"])
        count = int(request.data["count"])
        if pid <= 0 or count <= 0:
            return Response(status=400)
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            _, error = BasketService.add_to_db_basket(basket, pid, count)
            if error:
                status = 404 if error == "Product not found" else 400
                return Response({"error": error}, status=status)
            return self.get(request)
        product = Product.objects.filter(id=pid, available=True).first()
        if not product:
            return Response({"error": "Product not found"}, status=404)
        session_basket = get_session_basket(request)
        _, error = BasketService.add_to_session_basket(session_basket, pid, count, int(product.count))
        if error:
            return Response({"error": error}, status=400)
        request.session.modified = True
        return self.get(request)

    def delete(self, request):
        pid = int(request.data["id"])
        count = int(request.data["count"])
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            BasketService.remove_from_db_basket(basket, pid, count)
            return self.get(request)
        session_basket = get_session_basket(request)
        BasketService.remove_from_session_basket(session_basket, pid, count)
        request.session.modified = True
        return self.get(request)


class OrdersAPIView(APIView):
    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)
        basket = get_or_create_user_basket(request)
        order, error = OrderService.create_from_basket(request.user, basket)
        if error:
            return Response({"error": error}, status=400)
        return Response({"orderId": order.pk})


class OrderDetailAPIView(APIView):
    def get(self, request, order_id):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)
        order = Order.objects.filter(id=order_id, user=request.user).first()
        if not order:
            return Response({"error": "Order not found"}, status=404)
        return Response(OrderSerializer(order, context={"request": request}).data)

    def post(self, request, order_id):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)
        order = Order.objects.get(id=order_id, user=request.user)
        OrderService.confirm(
            order=order,
            delivery_type=request.data["deliveryType"],
            payment_type=request.data["paymentType"],
            city=request.data["city"],
            address=request.data["address"],
        )
        return Response({"orderId": order.id}, status=200)


class PaymentAPIView(APIView):
    def post(self, request, order_id):
        order = Order.objects.get(id=order_id, user=request.user)
        if not order:
            return Response(status=404)
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if PaymentService.validate(data["number"]):
            return Response({"error": "Card invalid"}, status=400)
        if PaymentService.is_expired(data["month"], data["year"]):
            return Response({"error": "Payment expired"}, status=400)
        error = PaymentService.process(order)
        if error:
            return Response({"error": error}, status=400)
        return Response(status=200)
