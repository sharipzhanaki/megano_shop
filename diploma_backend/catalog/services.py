import logging

from django.db.models import Count, Q, Value, IntegerField, Sum
from django.db.models.functions import Coalesce
from django.utils.timezone import now

from .models import Product, Sale

logger = logging.getLogger(__name__)


SORT_FIELD_MAP = {
    "rating": "rating",
    "price": "price",
    "reviews": "reviews_count",
    "date": "date",
}


def get_catalog_queryset(params):
    """Вернуть queryset товаров с фильтрацией и сортировкой по параметрам запроса."""
    queryset = (
        Product.objects
        .select_related("subcategory")
        .prefetch_related("images", "tags")
        .annotate(reviews_count=Count("reviews"))
    )
    name = params.get("filter[name]")
    if name:
        queryset = queryset.filter(title__icontains=name)
    min_price = params.get("filter[minPrice]")
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    max_price = params.get("filter[maxPrice]")
    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    if params.get("filter[freeDelivery]") in ("true", "1"):
        queryset = queryset.filter(free_delivery=True)
    if params.get("filter[available]") in ("true", "1"):
        queryset = queryset.filter(available=True, count__gt=0)
    category = params.get("category")
    if category:
        queryset = queryset.filter(subcategory_id=category)
    tags = params.getlist("tags[]") or params.getlist("tags")
    if tags:
        queryset = queryset.filter(tags__id__in=tags).distinct()
    sort = params.get("sort", "date")
    sort_type = params.get("sortType", "dec")
    field = SORT_FIELD_MAP.get(sort, "date")
    if sort_type == "dec":
        field = f"-{field}"
    return queryset.order_by(field)


def get_popular_products():
    """Вернуть топ-8 товаров по количеству оплаченных покупок и рейтингу."""
    return (
        Product.objects
        .prefetch_related("images", "tags")
        .annotate(
            reviews_count=Count("reviews", distinct=True),
            purchases=Coalesce(
                Sum("order_items__count", filter=Q(order_items__order__status="paid")),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by("-purchases", "-rating", "-reviews_count")[:8]
    )


def get_limited_products():
    """Вернуть последние 16 товаров с тегом 'limited'."""
    return (
        Product.objects
        .prefetch_related("images", "tags")
        .filter(tags__name__iexact="limited")
        .annotate(reviews_count=Count("reviews"))
        .order_by("-date")[:16]
    )


def get_banner_products():
    """Вернуть до 3 товаров с тегом 'banner' для главной страницы."""
    return (
        Product.objects
        .filter(tags__name__iexact="banner")
        .prefetch_related("images", "tags")
        .annotate(reviews_count=Count("reviews"))
        .order_by("-date")
        .distinct()[:3]
    )


def get_active_sales():
    """Вернуть акции, активные на сегодня, отсортированные по дате начала."""
    today = now().date()
    return (
        Sale.objects
        .filter(date_from__lte=today, date_to__gte=today)
        .select_related("product")
        .prefetch_related("product__images", "product__tags")
        .order_by("-date_from")
    )


class ReviewService:
    @staticmethod
    def create(product_id: int, data: dict):
        """Создать отзыв к товару. Возвращает (review, ошибка)."""
        from .models import Product
        from .serializers import ReviewSerializer
        product = Product.objects.filter(id=product_id).first()
        if not product:
            logger.warning("Review creation failed: product %s not found", product_id)
            return None, "Product not found"
        serializer = ReviewSerializer(data=data)
        if not serializer.is_valid():
            logger.warning("Review creation failed: invalid data for product %s: %s", product_id, serializer.errors)
            return None, serializer.errors
        review = serializer.save(product=product)
        logger.info("Review created for product %s by %s", product_id, data.get("author"))
        return review, None
