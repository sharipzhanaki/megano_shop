from django.urls import path
from .views import (
    CategoriesListAPIView, CatalogListAPIView, PopularProductsAPIView,
    LimitedProductsAPIView, BannerListAPIView, SalesListAPIView,
    ProductDetailAPIView, AddReviewAPIView, TagListAPIView
)


urlpatterns = [
    path("categories/", CategoriesListAPIView.as_view(), name="categories"),
    path("catalog/", CatalogListAPIView.as_view(), name="catalog"),
    path("products/popular/", PopularProductsAPIView.as_view(), name="products_popular"),
    path("products/limited/", LimitedProductsAPIView.as_view(), name="products_limited"),
    path("banners/", BannerListAPIView.as_view(), name="banners"),
    path("sales/", SalesListAPIView.as_view(), name="sales"),
    path("product/<int:id>/", ProductDetailAPIView.as_view(), name="product_detail"),
    path("product/<int:id>/reviews", AddReviewAPIView.as_view(), name="product_review"),
    path("tags/", TagListAPIView.as_view(), name="tags"),
]
