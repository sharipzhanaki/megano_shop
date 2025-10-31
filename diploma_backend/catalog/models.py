from django.db import models

class Category(models.Model):
    title = models.CharField(max_length=255)
    image_alt = models.CharField(max_length=255, blank=True, default="")
    image_src = models.CharField(max_length=255, blank=True, default="")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="subcategories", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Product(models.Model):
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
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    src = models.CharField(max_length=255)
    alt = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.src


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, related_name="specifications", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}: {self.value}"


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    email = models.EmailField()
    text = models.TextField()
    rate = models.PositiveSmallIntegerField(default=5)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} ({self.rate})"


class ProductSale(models.Model):
    product = models.ForeignKey(Product, related_name="sales", on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_from = models.CharField(max_length=10)
    date_to = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.product.title} sale {self.sale_price}"
