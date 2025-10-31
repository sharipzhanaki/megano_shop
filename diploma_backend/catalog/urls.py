from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CatalogViewSet, ProductDetailViewSet, TagViewSet

router = SimpleRouter()
router.register(r"catalog", CatalogViewSet, basename="catalog")
router.register(r"product", ProductDetailViewSet, basename="product")
router.register(r"tags", TagViewSet, basename="tags")

urlpatterns = [
    path("", include(router.urls)),
]
