import uuid
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User
from apps.products.models import Product


class Branch(models.Model):
    name = models.CharField(max_length=255)
    location = models.TextField()
    branch_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    contact_details = models.CharField(max_length=255)
    manager = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, related_name="managed_branch"
    )

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        ordering = ("name",)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.branch_code:
            self.branch_code = self.generate_branch_code()
        super().save(*args, **kwargs)

    def generate_branch_code(self):
        return f"{self.name[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"


class BranchProduct(models.Model):
    PRODUCT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branch_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='branch_products')
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=PRODUCT_STATUS_CHOICES, default='inactive')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('branch', 'product')
        ordering = ('product__name',)

    def __str__(self):
        return f"{self.product.name} at {self.branch.name}"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def product_name(self):
        return self.product.name

    @property
    def product_sku(self):
        return self.product.sku

    @property
    def product_category(self):
        return self.product.category.name if self.product.category else None

    @property
    def product_brand(self):
        return self.product.brand.name if self.product.brand else None


class ProductRequest(models.Model):
    REQUEST_STATUS = [
        ("pending", "Pending"),
        ("acknowledged", "Acknowledged"),
        ("fulfilled", "Fulfilled"),
    ]
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="requests"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default="pending")

    class Meta:
        ordering = ("-date_requested",)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} requested by {self.branch.name}"
