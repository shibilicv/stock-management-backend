import uuid
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
from django.db import models
from django.core.files import File


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    opening_stock = models.PositiveIntegerField()
    barcode_image = models.ImageField(upload_to="barcodes/", null=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        super().save(*args, **kwargs)

    def generate_sku(self):
        return f"{self.name[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

    def generate_barcode(self):
        if not self.barcode_image:
            code128 = Code128(self.sku, writer=ImageWriter())
            buffer = BytesIO()
            code128.write(buffer)
            self.barcode_image.save(f"{self.sku}.png", File(buffer), save=False)
            buffer.close()


class DamagedProduct(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="damages"
    )
    quantity = models.PositiveIntegerField()
    reason = models.TextField()
    date_reported = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date_reported",)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Deduct the damaged quantity from the product's quantity
        self.product.quantity -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)
