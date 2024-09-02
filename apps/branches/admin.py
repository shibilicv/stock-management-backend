from django.contrib import admin
from .models import Branch, ProductRequest, BranchProduct


admin.site.register(Branch)
admin.site.register(BranchProduct)
admin.site.register(ProductRequest)
