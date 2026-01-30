from rest_framework import serializers

from .models import Order, OrderItem
from catalog.serializers import ProductImageSerializer, ReviewSerializer, TagSerializer
from profile_user.models import Profile


class OrderProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id")
    category = serializers.IntegerField(source="product.category_id")
    title = serializers.CharField(source="product.title")
    description = serializers.CharField(source="product.description")
    freeDelivery = serializers.BooleanField(source="product.free_delivery")
    images = ProductImageSerializer(source="product.images", many=True)
    tags = TagSerializer(source="product.tags", many=True)
    rating = serializers.FloatField(source="product.rating")
    reviews = ReviewSerializer(source="product.reviews", many=True)
    count = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    date = serializers.DateTimeField(source="product.date", required=False)

    class Meta:
        model = OrderItem
        fields = (
            "id", "category", "count", "price",
            "date", "title", "description", "freeDelivery",
            "images", "tags", "reviews", "rating",
        )


class OrderSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at")
    fullName = serializers.CharField(source="user.profile.full_name")
    email = serializers.EmailField(source="user.profile.email")
    phone = serializers.CharField(source="user.profile.phone")
    deliveryType = serializers.CharField(source="delivery_type")
    paymentType = serializers.CharField(source="payment_type")
    totalCost = serializers.DecimalField(source="total_cost", max_digits=10, decimal_places=2)
    products = OrderProductSerializer(source="items", many=True)
    paymentError = serializers.CharField(source="payment_error")

    class Meta:
        model = Order
        fields = (
            "id", "createdAt", "fullName", "email",
            "phone", "deliveryType", "paymentType", "totalCost",
            "status", "city", "address", "products", "paymentError",
        )


class PaymentSerializer(serializers.Serializer):
    number = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    month = serializers.CharField(required=False, allow_blank=True)
    year = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
