from django.utils.timezone import now
from django.db import transaction
from django.db.models import Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import BasketItem, Order, OrderItem
from .serializers import OrderSerializer, PaymentSerializer
from .services import DeliveryCalculator, PaymentService
from .utils import get_session_basket, get_or_create_user_basket
from catalog.models import Product, Sale
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
        if pid <= 0 or count <= 0:
            return Response(status=400)
        product = Product.objects.filter(id=pid, available=True).first()
        if not product:
            return Response({"error": "Product not found"}, status=404)
        stock = int(product.count)
        if request.user.is_authenticated:
            basket = get_or_create_user_basket(request)
            item, _ = BasketItem.objects.get_or_create(
                basket=basket,
                product_id=pid,
                defaults={"count": 0},
            )
            already = int(item.count)
            can_add = max(0, stock - already)
            add = min(count, can_add)
            if add == 0:
                return Response({"error": "Not enough stock"}, status=400)
            item.count = already + add
            item.save(update_fields=["count"])
            return self.get(request)
        session_basket = get_session_basket(request)
        key = str(pid)
        already = int(session_basket.get(key, 0))
        can_add = max(0, stock - already)
        add = min(count, can_add)
        if add == 0:
            return Response({"error": "Not enough stock"}, status=400)
        session_basket[key] = already + add
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
        orders = Order.objects.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)
        basket = get_or_create_user_basket(request)
        items = BasketItem.objects.filter(basket=basket).select_related("product")
        if not items.exists():
            return Response({"error": "Basket is empty"}, status=400)
        today = now().date()
        subtotal = 0
        order = Order.objects.create(user=request.user, total_cost=0)
        order_items = []
        for item in items:
            sale_price = (
                Sale.objects
                .filter(product=item.product, date_from__lte=today, date_to__gte=today)
                .values_list("sale_price", flat=True)
                .first()
            )
            unit_price = sale_price if sale_price is not None else item.product.price
            subtotal += unit_price * item.count
            order_items.append(OrderItem(
                order=order,
                product=item.product,
                count=item.count,
                price=unit_price,
            ))
        OrderItem.objects.bulk_create(order_items)
        order.total_cost = subtotal
        order.save(update_fields=["total_cost"])
        items.delete()
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
        delivery_type = request.data["deliveryType"]
        payment_type = request.data["paymentType"]
        city = request.data["city"]
        address = request.data["address"]
        order.delivery_type = delivery_type
        order.payment_type = payment_type
        order.city = city
        order.address = address
        subtotal = (
                OrderItem.objects
                .filter(order=order)
                .aggregate(s=Sum(F("price") * F("count")))
                .get("s") or 0
        )
        delivery_price = DeliveryCalculator.calculate(
            subtotal=subtotal,
            delivery_type=delivery_type,
        )
        order.total_cost = subtotal + delivery_price
        order.status = "accepted"
        order.save(update_fields=[
            "delivery_type", "payment_type", "city", "address", "total_cost", "status"
        ])
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
        items = list(OrderItem.objects.filter(order=order).select_related("product"))
        for item in items:
            if item.product.count < item.count:
                return Response({"error": "Not enough stock"}, status=400)
        for item in items:
            Product.objects.filter(id=item.product.id).update(count=F("count") - item.count)
        Product.objects.filter(id__in=[i.product.id for i in items], count__lte=0).update(available=False)
        order.status = "paid"
        order.save(update_fields=["status"])
        return Response(status=200)
