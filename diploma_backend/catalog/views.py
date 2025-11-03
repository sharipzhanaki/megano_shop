from django.db.models import Count, Prefetch
from django_filters import rest_framework as filters
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import Product, Category, Tag, ProductSale, Review
from .serializers import (
    ProductShortSerializer,
    ProductFullSerializer,
    CatalogItemSerializer,
    ReviewSerializer,
    ProductSaleSerializer,
    TagSerializer,
)
from .pagination import FrontPagePagination

class ProductFilter(filters.FilterSet):
    """Фильтры под каталог /catalog"""
    name = filters.CharFilter(field_name="title", lookup_expr="icontains")
    category = filters.NumberFilter(field_name="category_id")
    minPrice = filters.NumberFilter(field_name="price", lookup_expr="gte")
    maxPrice = filters.NumberFilter(field_name="price", lookup_expr="lte")
    freeDelivery = filters.BooleanFilter(field_name="free_delivery")
    available = filters.BooleanFilter(field_name="available")
    tags = filters.ModelMultipleChoiceFilter(field_name="tags", queryset=Tag.objects.all())

    class Meta:
        model = Product
        fields = ["name", "category", "minPrice", "maxPrice", "freeDelivery", "available", "tags"]


class CategoryViewSet(ReadOnlyModelViewSet):
    """
    GET /api/categories — верхние категории с подкатегориями
    """
    serializer_class = CatalogItemSerializer
    pagination_class = None
    http_method_names = ["get"]

    def get_queryset(self):
        return (
            Category.objects
            .filter(parent__isnull=True)
            .only("id", "title", "image_src", "image_alt")
            .prefetch_related("subcategories")
        )


class CatalogViewSet(ReadOnlyModelViewSet):
    """
    /catalog - список товаров с фильтрацией, сортировкой, пагинацией
    /products/popular
    /products/limited
    /sales
    /banners
    """
    serializer_class = ProductShortSerializer
    pagination_class = FrontPagePagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description"]
    ordering_fields = ["price", "rating", "reviews", "date"]
    ordering = ["-date"]

    queryset = (
        Product.objects
        .select_related("category")
        .prefetch_related("images", "tags")
        .only(
            "id", "category", "title", "price", "count",
            "date", "description", "free_delivery", "rating"
        )
        .defer("full_description")
    )

    def list(self, request, *args, **kwargs):
        sort = request.query_params.get("sort", "date")
        sort_type = request.query_params.get("sortType", "dec")
        queryset = self.filter_queryset(self.get_queryset().annotate(reviews_count=Count("reviews")))
        field_map = {
            "rating": "rating",
            "price": "price",
            "reviews": "reviews_count",
            "date": "date"
        }
        order_field = field_map.get(sort, "date")
        if sort_type == "dec":
            order_field = f"-{order_field}"

        queryset = queryset.order_by(order_field)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="products/popular")
    def popular(self, request):
        """GET /products/popular - топ товаров по рейтингу/отзывам"""
        queryset = (
            self.get_queryset()
            .annotate(reviews=Count("reviews"))
            .order_by("-rating", "-reviews")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="products/limited")
    def limited(self, request):
        """GET /products/limited - товары с низким остатком"""
        queryset = self.get_queryset().filter(count__lte=5).order_by("count")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="sales")
    def sales(self, request):
        """GET /sales - товары, участвующие в акциях"""
        queryset = ProductSale.objects.select_related("product").prefetch_related(
            Prefetch("product__images"),
            Prefetch("product__tags"),
        )
        serializer = ProductSaleSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="banners")
    def banners(self, request):
        """GET /banners - товары с тегом 'banner'"""
        queryset = (
            self.get_queryset()
            .filter(tags__name__iexact="banner")
            .distinct()
            .order_by("-date")
        )
        return Response(self.get_serializer(queryset, many=True).data)


class ProductDetailViewSet(ReadOnlyModelViewSet):
    """
    /product/{id} - детальная информация о товаре с отзывами, тегами, характеристиками.
    """
    serializer_class = ProductFullSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Product.objects
            .select_related("category")
            .prefetch_related(
                "images", "tags", "specifications",
                Prefetch("reviews", queryset=Review.objects.only(
                    "id", "author", "email", "text", "rate", "date", "product_id"
                )),
            )
        )

    @action(detail=True, methods=["post"], url_path="review")
    def add_review(self, request, pk=None):
        """POST /product/{id}/review - добавить отзыв"""
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """GET /tags - список тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
