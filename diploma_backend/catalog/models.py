from django.db import models


def category_images_directory_path(instance, filename: str) -> str:
    return f"categories/category_{instance.pk}/images/{filename}"


def product_images_directory_path(instance: "ProductImage", filename: str) -> str:
    return f"products/product_{instance.product.pk}/images/{filename}"


class Category(models.Model):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    title = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="subcategories", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=category_images_directory_path, blank=True, null=True)
    image_alt = models.CharField(max_length=255, blank=True, null=True)

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
    description = models.TextField(blank=True)
    full_description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    free_delivery = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    rating = models.FloatField(default=0.0)
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    class Meta:
        verbose_name = "Product image"
        verbose_name_plural = "Product images"

    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_images_directory_path)
    alt = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.image.name


class ProductSpecification(models.Model):
    class Meta:
        verbose_name = "Specification"
        verbose_name_plural = "Specifications"

    product = models.ForeignKey(Product, related_name="specifications", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.value}"


class Review(models.Model):
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    email = models.EmailField()
    text = models.TextField()
    rate = models.PositiveSmallIntegerField(default=5)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} ({self.rate})"


class Sale(models.Model):
    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    product = models.ForeignKey(Product, related_name="sales", on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_from = models.DateField()
    date_to = models.DateField()

    def __str__(self):
        return f"{self.product.title} sale {self.sale_price}"
