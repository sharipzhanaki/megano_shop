from django.contrib import admin

from .models import (
    Category, Product, ProductImage,
    ProductSpecification, Sale, Review, Tag
)

class ProductImageInline(admin.TabularInline):
    """Вкладка для изображений товара"""
    model = ProductImage
    extra = 1


class ProductSpecificationInline(admin.TabularInline):
    """Вкладка для характеристик"""
    model = ProductSpecification
    extra = 1


class ReviewInline(admin.TabularInline):
    """Вкладка для отзывов"""
    model = Review
    extra = 0
    readonly_fields = ("author", "email", "text", "rate", "date")
    can_delete = True


class ProductSaleInline(admin.TabularInline):
    """Вкладка для акций"""
    model = Sale
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Основная модель товаров"""
    list_display = (
        "id", "title", "category", "price", "count",
        "free_delivery", "available", "rating"
    )
    list_filter = ("category", "free_delivery", "available", "tags")
    search_fields = ("title", "description", "category__title")
    ordering = ("-date",)
    list_per_page = 20
    inlines = [
        ProductImageInline,
        ProductSpecificationInline,
        ProductSaleInline,
        ReviewInline,
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("category")
            .prefetch_related("images", "tags", "specifications", "reviews", "sales")
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Категории и подкатегории"""
    list_display = ("id", "title", "parent")
    list_filter = ("parent",)
    search_fields = ("title",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Теги"""
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Отзывы"""
    list_display = ("id", "product", "author", "rate", "date")
    list_filter = ("rate", "date")
    search_fields = ("author", "text", "product__title")
    readonly_fields = ("date",)


@admin.register(Sale)
class ProductSaleAdmin(admin.ModelAdmin):
    """Акции"""
    list_display = ("id", "product", "sale_price", "date_from", "date_to")
    list_filter = ("date_from", "date_to")
    search_fields = ("product__title",)
