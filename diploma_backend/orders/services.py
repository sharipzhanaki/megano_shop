import datetime
import logging

from django.db.models import Sum, F
from django.utils.timezone import now

from .models import Basket, BasketItem, DeliverySettings, Order, OrderItem
from catalog.models import Product, Sale

logger = logging.getLogger(__name__)


class DeliveryCalculator:
    """
    Расчёт доставки по ТЗ, значения из админки.
    - express: фиксированная стоимость
    - ordinary: бесплатно от порога, иначе фикс
    """
    @staticmethod
    def get_settings() -> DeliverySettings:
        settings = DeliverySettings.objects.order_by("id").first()
        if settings:
            return settings
        return DeliverySettings()

    @classmethod
    def calculate(cls, *, subtotal, delivery_type: str):
        s = cls.get_settings()
        if delivery_type == "express":
            return s.express_delivery_price
        if subtotal >= s.free_delivery:
            return 0
        return s.default_delivery_price


class BasketService:
    @staticmethod
    def add_to_db_basket(basket: Basket, pid: int, count: int):
        """Добавить товар в корзину пользователя. Возвращает (добавлено, ошибка)."""
        product = Product.objects.filter(id=pid, available=True).first()
        if not product:
            logger.warning("Add to basket failed: product %s not found or unavailable", pid)
            return None, "Product not found"
        item, _ = BasketItem.objects.get_or_create(basket=basket, product_id=pid, defaults={"count": 0})
        can_add = max(0, int(product.count) - int(item.count))
        add = min(count, can_add)
        if add == 0:
            logger.warning("Add to basket failed: not enough stock for product %s", pid)
            return None, "Not enough stock"
        item.count += add
        item.save(update_fields=["count"])
        logger.debug("Added %d of product %s to basket %s", add, pid, basket.id)
        return add, None

    @staticmethod
    def add_to_session_basket(session_basket: dict, pid: int, count: int, stock: int):
        """Добавить товар в сессионную корзину. Возвращает (добавлено, ошибка)."""
        already = int(session_basket.get(str(pid), 0))
        can_add = max(0, stock - already)
        add = min(count, can_add)
        if add == 0:
            return None, "Not enough stock"
        session_basket[str(pid)] = already + add
        return add, None

    @staticmethod
    def remove_from_db_basket(basket: Basket, pid: int, count: int) -> None:
        item = BasketItem.objects.filter(basket=basket, product_id=pid).first()
        if item:
            item.count -= count
            if item.count <= 0:
                item.delete()
            else:
                item.save()

    @staticmethod
    def remove_from_session_basket(session_basket: dict, pid: int, count: int) -> None:
        key = str(pid)
        if key in session_basket:
            session_basket[key] -= count
            if session_basket[key] <= 0:
                del session_basket[key]


class OrderService:
    @staticmethod
    def create_from_basket(user, basket: Basket):
        """Создать заказ из корзины, рассчитать цены с учётом акций, очистить корзину.
        Возвращает (order, ошибка)."""
        items = BasketItem.objects.filter(basket=basket).select_related("product")
        if not items.exists():
            logger.warning("Order creation failed: basket is empty for user %s", user.username)
            return None, "Basket is empty"
        today = now().date()
        subtotal = 0
        order = Order.objects.create(user=user, total_cost=0)
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
        logger.info("Order #%s created for user %s, total=%s", order.id, user.username, subtotal)
        return order, None

    @staticmethod
    def confirm(order: Order, delivery_type: str, payment_type: str, city: str, address: str) -> None:
        """Подтвердить заказ: записать доставку, рассчитать итог, сменить статус на accepted."""
        subtotal = (
            OrderItem.objects
            .filter(order=order)
            .aggregate(s=Sum(F("price") * F("count")))
            .get("s") or 0
        )
        delivery_price = DeliveryCalculator.calculate(subtotal=subtotal, delivery_type=delivery_type)
        order.delivery_type = delivery_type
        order.payment_type = payment_type
        order.city = city
        order.address = address
        order.total_cost = subtotal + delivery_price
        order.status = "accepted"
        order.save(update_fields=[
            "delivery_type", "payment_type", "city", "address", "total_cost", "status"
        ])


class PaymentService:
    @staticmethod
    def validate(number: str) -> str | None:
        if number is None:
            return "Number is required"
        n = number.strip()
        if not n.isdigit():
            return "Number must be digits only"
        if len(n) > 8:
            return "Number must be at most 8 digits"
        if int(n) % 2 != 0:
            return "Number must be even"
        return None

    @staticmethod
    def is_expired(month: str, year: str) -> bool:
        if not month or not year:
            return False
        m = int(month)
        y = int(year)
        if m < 1 or m > 12:
            return True
        if y >= 100:
            y = y % 100
        now = datetime.datetime.now()
        now_y = now.year % 100
        now_m = now.month
        return (y < now_y) or (y == now_y and m < now_m)

    @staticmethod
    def process(order: Order) -> str | None:
        """Провести оплату: проверить остатки, списать товар, сменить статус на paid.
        Возвращает строку с ошибкой или None при успехе."""
        items = list(OrderItem.objects.filter(order=order).select_related("product"))
        for item in items:
            if item.product.count < item.count:
                return "Not enough stock"
        for item in items:
            Product.objects.filter(id=item.product.id).update(count=F("count") - item.count)
        Product.objects.filter(
            id__in=[i.product.id for i in items], count__lte=0
        ).update(available=False)
        order.status = "paid"
        order.save(update_fields=["status"])
        logger.info("Order #%s payment processed successfully", order.id)
        return None
