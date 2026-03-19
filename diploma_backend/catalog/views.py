from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from .models import Product, Category, Tag
from .serializers import (
    ProductShortSerializer,
    ProductFullSerializer,
    CatalogItemSerializer,
    ReviewSerializer,
    SaleSerializer,
    TagSerializer,
)
from .pagination import FrontPagePagination
from .services import (
    get_catalog_queryset,
    get_popular_products,
    get_limited_products,
    get_banner_products,
    get_active_sales,
    ReviewService,
)


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
        return get_catalog_queryset(self.request.query_params)


class PopularProductsAPIView(ListAPIView):
    """GET /products/popular - топ 8 часто покупаемых товаров с хорошим рейтингом"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return get_popular_products()


class LimitedProductsAPIView(ListAPIView):
    """GET /products/limited - товары с тегом 'limited' - слайдер с ограниченным тиражом"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return get_limited_products()


class BannerListAPIView(ListAPIView):
    """GET /banners - товары с тегом 'banner' - реклама на главной странице"""
    serializer_class = ProductShortSerializer

    def get_queryset(self):
        return get_banner_products()


class SalesListAPIView(ListAPIView):
    """GET /sales - товары, участвующие в акциях"""
    serializer_class = SaleSerializer
    pagination_class = FrontPagePagination

    def get_queryset(self):
        return get_active_sales()


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
        review, error = ReviewService.create(product_id=id, data=request.data)
        if error:
            status = 404 if error == "Product not found" else 400
            return Response({"error": error}, status=status)
        return Response(ReviewSerializer(review).data, status=201)


class TagListAPIView(ListAPIView):
    """GET /tags - список тегов"""
    serializer_class = TagSerializer
    pagination_class = None

    def get_queryset(self):
        return Tag.objects.all()
