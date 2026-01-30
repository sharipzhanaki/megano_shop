import datetime

from .models import DeliverySettings


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
        if y >= 100:
            y = y % 100
        now = datetime.datetime.now()
        now_y = now.year % 100
        now_m = now.month
        return (y < now_y) or (y == now_y and m < now_m)
