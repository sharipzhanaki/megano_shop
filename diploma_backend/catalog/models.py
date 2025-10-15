from django.db import models


class Category(models.Model):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    title = models.CharField(max_length=255)
    image_alt = models.CharField(max_length=255, blank=True, default="")
    image_src = models.CharField(max_length=155, blank=True, default="")

    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="subcategories", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title


class Tag(models.Model):
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    full_description = models.TextField(blank=True, default="")
    price = models.DecimalField(decimal_places=2)
    count = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    free_delivery = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    rating = models.FloatField(default=0.0)
    reviews = models.PositiveIntegerField(default=0)

    tags = models.ManyToManyField(Tag, related_name="products", blank=True)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    product = models.ForeignKey(Product, related_name="image", on_delete=models.CASCADE)
    src = models.CharField(max_length=255)
    alt = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.src

