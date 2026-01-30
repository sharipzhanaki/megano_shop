from django.db import transaction
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import BasketItem, Order, OrderItem
from .serializers import OrderSerializer, PaymentSerializer
from .services import DeliveryCalculator, PaymentService
from .utils import get_session_basket, get_or_create_user_basket
from catalog.models import Product
from catalog.serializers import ProductShortSerializer
from profile_user.models import Profile


class BasketAPIView(APIView):
    def get(self, request):
        items = []
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            queryset = BasketItem.objects.filter(basket=basket).select_related("product")
            for item in queryset:
                data = ProductShortSerializer(item.product, context={"request": request}).data
                data["count"] = item.count
                items.append(data)
            return Response(items)
        session_basket = get_session_basket(request)
        for pid, count in session_basket.items():
            product = Product.objects.get(id=int(pid))
            data = ProductShortSerializer(product, context={"request": request}).data
            data["count"] = int(count)
            items.append(data)
        return Response(items)

    def post(self, request):
        pid = int(request.data["id"])
        count = int(request.data["count"])
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            item, created = BasketItem.objects.get_or_create(
                basket=basket,
                product_id=pid,
                defaults={"count": count},
            )
            if not created:
                item.count += int(count)
                item.save()
            return self.get(request)
        session_basket = get_session_basket(request)
        key = str(pid)
        session_basket[key] = int(session_basket.get(key, 0)) + int(count)
        request.session.modified = True
        return self.get(request)

    def delete(self, request):
        pid = int(request.data["id"])
        count = int(request.data["count"])
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            item = BasketItem.objects.filter(basket=basket, product_id=pid).first()
            if item:
                item.count -= count
                if item.count <= 0:
                    item.delete()
                else:
                    item.save()
            return self.get(request)
        session_basket = get_session_basket(request)
        key = str(pid)
        if key in session_basket:
            session_basket[key] -= count
            if session_basket[key] <= 0:
                del session_basket[key]
            request.session.modified = True
        return self.get(request)


class OrdersAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response([], status=200)
        orders = Order.objects.filter(user=request.user)
        serialized = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serialized.data)

    @transaction.atomic
    def post(self, request):
        basket = get_or_create_user_basket(request)
        items = BasketItem.objects.filter(basket=basket).select_related("product")
        subtotal = sum(i.product.price * i.count for i in items)
        order = Order.objects.create(user=request.user, total_cost=subtotal)
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item.product,
                count=item.count,
                price=item.product.price * item.count,
            )for item in items
        ])
        items.delete()
        return Response({"orderId": order.pk})


class OrderDetailAPIView(APIView):
    def get(self, request, order_id):
        order = Order.objects.filter(id=order_id, user=request.user).first()
        if not order:
            return Response(status=404)
        serialized = OrderSerializer(order, context={"request": request})
        return Response(serialized.data)

    def post(self, request, order_id):
        order = Order.objects.get(id=order_id, user=request.user)
        delivery_type = request.data["deliveryType"]
        payment_type = request.data["paymentType"]
        city = request.data["city"]
        address = request.data["address"]
        order.delivery_type = delivery_type
        order.payment_type = payment_type
        order.city = city
        order.address = address
        subtotal = order.items.aggregate(s=Sum("price")).get("s") or 0
        delivery_price = DeliveryCalculator.calculate(
            subtotal=subtotal,
            delivery_type=delivery_type,
        )
        order.total_cost = subtotal + delivery_price
        order.save(update_fields=["delivery_type", "payment_type", "city", "address", "total_cost"])
        return Response({"orderId": order.id}, status=200)


class PaymentAPIView(APIView):
    def post(self, request, order_id):
        order = Order.objects.get(id=order_id, user=request.user)
        if not order:
            return Response(status=404)
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        card_number = data["number"]
        month = data["month"]
        year = data["year"]
        if PaymentService.is_expired(month, year):
            order.payment_error = "Payment expired"
            order.save(update_fields=["payment_error"])
            return Response({"error": "Payment expired"}, status=500)
        if PaymentService.validate(card_number):
            order.payment_error = "Card invalid"
            order.save(update_fields=["payment_error"])
            return Response({"error": "Card invalid"}, status=400)
        order.status = "paid"
        order.payment_error = ""
        order.save(update_fields=["status", "payment_error"])
        return Response(status=200)
