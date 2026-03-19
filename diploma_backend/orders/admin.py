from django.contrib import admin

from .models import Basket, BasketItem, Order, OrderItem, DeliverySettings


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username", "user__email")
    inlines = (BasketItemInline,)


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("id", "basket", "product", "count")
    list_select_related = ("basket", "product")
    search_fields = ("basket__user__username", "product__title")


@admin.register(DeliverySettings)
class DeliveryPriceAdmin(admin.ModelAdmin):
    list_display = ("default_delivery_price", "free_delivery", "express_delivery_price")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)
    fields = ("product", "count", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "delivery_type", "payment_type", "total_cost", "created_at")
    list_filter = ("status", "delivery_type", "payment_type", "created_at")
    search_fields = ("id", "user__username", "user__email", "city", "address")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    inlines = (OrderItemInline,)
    fieldsets = (
        ("Order", {"fields": ("user", "status", "created_at")}),
        ("Delivery & Payment", {"fields": ("delivery_type", "payment_type", "total_cost")}),
        ("Address", {"fields": ("city", "address")}),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "count", "price")
    list_select_related = ("order", "product")
    search_fields = ("order__id", "product__title")
    autocomplete_fields = ("order", "product")
