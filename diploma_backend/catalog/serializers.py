from rest_framework import serializers
from .models import Category, Product, ProductImage, Tag

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("src", "alt")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class ProductShortSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title", "description",
            "free_delivery", "images", "tags", "reviews", "rating",
        )
        extra_kwargs = {}


class CategoryImageSerializer(serializers.ModelSerializer):
    src = serializers.CharField()
    alt = serializers.CharField()

class SubCategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", )

    def get_image(self, obj):
        return {"src": obj.image_src, "alt": obj.image_alt}


class CatalogItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")

    def get_image(self, obj):
        return {"src": obj.image_src, "alt": obj.image_alt}
