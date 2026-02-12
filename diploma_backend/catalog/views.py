from django.db.models import Count, Q, Value, IntegerField, Sum
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from .models import Product, Category, Tag, Sale
from .serializers import (
    ProductShortSerializer,
    ProductFullSerializer,
    CatalogItemSerializer,
    ReviewSerializer,
    SaleSerializer,
    TagSerializer,
)
from .pagination import FrontPagePagination


class CategoriesListAPIView(ListAPIView):
    """GET /api/categories — верхние категории с подкатегориями"""
    serializer_class = CatalogItemSerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.prefetch_related("subcategories")


class CatalogListAPIView(ListAPIView):
    """GET /catalog - список товаров с фильтрацией, сортировкой, пагинацией"""
    serializer_class = ProductShortSerializer
    pagination_class = FrontPagePagination

    def get_queryset(self):
        queryset = (
            Product.objects
            .select_related("subcategory")
            .prefetch_related("images", "tags")
            .annotate(reviews_count=Count("reviews"))
        )
        q = self.request.query_params
        name = q.get("filter[name]")
        if name:
            queryset = queryset.filter(title__icontains=name)
        min_price = q.get("filter[minPrice]")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        max_price = q.get("filter[maxPrice]")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        free_delivery = q.get("filter[freeDelivery]")
        if free_delivery in ("true", "1"):
            queryset = queryset.filter(free_delivery=True)
        available = q.get("filter[available]")
        if available in ("true", "1"):
            queryset = queryset.filter(available=True, count__gt=0)
        category = q.get("category")
        if category:
            queryset = queryset.filter(subcategory_id=category)
        tags = q.getlist("tags[]") or q.getlist("tags")
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()
        sort = q.get("sort", "date")
        sort_type = q.get("sortType", "dec")
        sort_map = {
            "rating": "rating",
            "price": "price",
            "reviews": "reviews_count",
            "date": "date",
        }
        field = sort_map.get(sort, "date")
        if sort_type == "dec":
            field = f"-{field}"
        queryset = queryset.order_by(field)
        return queryset


class PopularProductsAPIView(ListAPIView):
    """GET /products/popular - топ 8 часто покупаемых товаров с хорошим рейтингом"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return (
            Product.objects
            .prefetch_related("images", "tags")
            .annotate(reviews_count=Count("reviews", distinct=True),
                      purchases=Coalesce(Sum(
                          "order_items__count",
                          filter=Q(order_items__order__status="paid"),
                      ), Value(0), output_field=IntegerField()))
        .order_by("-purchases", "-rating", "-reviews_count")[:8]
        )


class LimitedProductsAPIView(ListAPIView):
    """GET /products/limited - товары с тегом 'limited' - слайдер с ограниченным тиражом"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return (
            Product.objects
            .prefetch_related("images", "tags")
            .filter(tags__name__iexact="limited")
            .annotate(reviews_count=Count("reviews"))
            .order_by("-date")[:16]
        )


class BannerListAPIView(ListAPIView):
    """GET /banners - товары с тегом 'banner' - реклама на главной странице"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return (
            Product.objects
            .filter(tags__name__iexact="banner")
            .prefetch_related("images", "tags")
            .annotate(reviews_count=Count("reviews"))
            .order_by("-date").distinct()[:3]
        )


class SalesListAPIView(ListAPIView):
    """GET /sales - товары, участвующие в акциях"""
    serializer_class = SaleSerializer
    pagination_class = FrontPagePagination

    def get_queryset(self):
        today = now().date()
        return (
            Sale.objects
            .filter(date_from__lte=today, date_to__gte=today)
            .select_related("product")
            .prefetch_related("product__images", "product__tags")
            .order_by("-date_from")
        )


class ProductDetailAPIView(RetrieveAPIView):
    """GET /product/{id} - детальная информация о товаре с отзывами, тегами, характеристиками"""
    serializer_class = ProductFullSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return (
            Product.objects
            .select_related("subcategory")
            .prefetch_related("images", "tags", "specifications", "reviews")
        )


class AddReviewAPIView(APIView):
    """POST /product/{id}/review - добавить отзыв товару"""
    def post(self, request, id):
        product = Product.objects.filter(id=id).first()
        if not product:
            return Response({"error": "Product not found"}, status=404)
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=201)


class TagListAPIView(ListAPIView):
    """GET /tags - список тегов"""
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.all()
