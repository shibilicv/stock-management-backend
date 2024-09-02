from django.db import models
from django.db.models import F
from apps.products.models import Product, DamagedProduct
from apps.suppliers.models import Supplier
from apps.branches.models import Branch, BranchProduct


class ProductInflow(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="productinflow"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="productinflow"
    )
    quantity_received = models.PositiveIntegerField()
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    date_received = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ("-date_received",)

    def __str__(self):
        return (
            f"{self.quantity_received} x {self.product.name} from {self.supplier.name}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.product.quantity = F("quantity") + self.quantity_received
        self.product.save()


class ProductOutflow(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="productoutflow"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="productoutflow"
    )
    quantity_sent = models.PositiveIntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    date_sent = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ("-date_sent",)

    def __str__(self):
        return f"{self.quantity_sent} x {self.product.name} to {self.branch.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update or create BranchProduct
        branch_product, created = BranchProduct.objects.get_or_create(
            branch=self.branch,
            product=self.product,
            defaults={"quantity": self.quantity_sent},
        )

        if not created:
            branch_product.quantity = F("quantity") + self.quantity_sent
            branch_product.save()

        # Decrease quantity in central store
        self.product.quantity = F("quantity") - self.quantity_sent
        self.product.save()
