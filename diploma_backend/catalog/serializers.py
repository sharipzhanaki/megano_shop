from rest_framework import serializers

from .models import (
    Category, Subcategory, Product, ProductImage,
    Tag, ProductSpecification, Review, Sale
)


class ProductImageSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("src", "alt")

    def get_src(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""


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


class SaleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id")
    title = serializers.CharField(source="product.title")
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2)
    salePrice = serializers.DecimalField(source="sale_price", max_digits=10, decimal_places=2)
    images = ProductImageSerializer(source="product.images", many=True)
    dateFrom = serializers.SerializerMethodField()
    dateTo = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ("id", "title", "price", "salePrice", "dateFrom", "dateTo", "images")

    def get_dateFrom(self, obj):
        return obj.date_from.strftime("%m-%d")

    def get_dateTo(self, obj):
        return obj.date_to.strftime("%m-%d")


class ProductShortSerializer(serializers.ModelSerializer):
    freeDelivery = serializers.BooleanField(source="free_delivery")
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True)
    rating = serializers.FloatField()
    reviews = serializers.IntegerField(source="reviews_count", read_only=True)
    category = serializers.IntegerField(source="subcategory.id", read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title", "description",
            "freeDelivery", "images", "tags", "reviews", "rating"
        )

    def get_price(self, obj):
        sale_price = obj.sales.first()
        if sale_price:
            obj.price = sale_price.sale_price
        return obj.price


class ProductFullSerializer(serializers.ModelSerializer):
    freeDelivery = serializers.BooleanField(source="free_delivery")
    fullDescription = serializers.CharField(source="full_description")
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True)
    reviews = ReviewSerializer(many=True)
    specifications = ProductSpecificationSerializer(many=True)
    category = serializers.IntegerField(source="subcategory.id", read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "category", "title", "price", "count", "date",
            "description", "fullDescription", "freeDelivery", "images",
            "tags", "reviews", "specifications", "rating"
        )

    def get_price(self, obj):
        sale_price = obj.sales.first()
        if sale_price:
            obj.price = sale_price.sale_price
        return obj.price


class CategoryImageSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, obj):
        request = self.context.get("request")
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_alt(self, obj):
        return obj.image_alt or ""


class SubCategorySerializer(serializers.ModelSerializer):
    image = CategoryImageSerializer(source="*", read_only=True)

    class Meta:
        model = Subcategory
        fields = ("id", "title", "image")


class CatalogItemSerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True)
    image = CategoryImageSerializer(source="*", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")
