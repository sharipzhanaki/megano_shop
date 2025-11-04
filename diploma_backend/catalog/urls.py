from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    CategoryViewSet, CatalogViewSet, ProductDetailViewSet, TagViewSet, ProductSalesViewSet
)

router = SimpleRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"catalog", CatalogViewSet, basename="catalog")
router.register(r"product", ProductDetailViewSet, basename="product")
router.register(r"tags", TagViewSet, basename="tags")
router.register(r"sales", ProductSalesViewSet, basename="sales")

urlpatterns = [
    path("", include(router.urls)),
    path("banners/", CatalogViewSet.as_view({"get": "banners"}), name="banners"),
]
