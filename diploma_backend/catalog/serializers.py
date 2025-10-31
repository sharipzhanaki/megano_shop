from rest_framework import serializers
from .models import Category, Product, ProductImage, Tag, ProductSpecification, Review, ProductSale

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("src", "alt")


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ("name", "value")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "author", "email", "text", "rate", "date")


class ProductSaleSerializer(serializers.ModelSerializer):
    dateFrom = serializers.CharField(source="date_from")
    dateTo = serializers.CharField(source="date_to")
    salePrice = serializers.DecimalField(source="sale_price", max_digits=10, decimal_places=2)

    class Meta:
        model = ProductSale
        fields = ("id", "price", "salePrice", "dateFrom", "dateTo", "title", "images")


class ProductShortSerializer(serializers.ModelSerializer):
    freeDelivery = serializers.BooleanField(source="free_delivery")
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    rating = serializers.FloatField()
    reviews = serializers.IntegerField(source="reviews.count", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title", "description",
            "freeDelivery", "images", "tags", "reviews", "rating"
        )


class ProductFullSerializer(serializers.ModelSerializer):
    freeDelivery = serializers.BooleanField(source="free_delivery")
    fullDescription = serializers.CharField(source="full_description")
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = (
            "id", "category", "title", "price", "count", "date",
            "description", "fullDescription", "freeDelivery", "images",
            "tags", "reviews", "specifications", "rating"
        )


class SubCategorySerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "images")


class CatalogItemSerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "images", "subcategories")
