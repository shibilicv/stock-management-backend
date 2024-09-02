from rest_framework import serializers
from .models import Branch, ProductRequest, BranchProduct


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'location', 'branch_code', 'contact_details', 'manager']
        read_only_fields = ['id', 'branch_code']


class BranchProductSerializer(serializers.ModelSerializer):
    product_barcode = serializers.CharField(source='product.barcode_image', read_only=True)

    class Meta:
        model = BranchProduct
        fields = ['id', 'product_name', 'product_sku', 'product_barcode', 'product_category', 'product_brand', 'quantity', 'status', 'last_updated']


class UpdateBranchProductQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchProduct
        fields = ['quantity']


class ProductRequestSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductRequest
        fields = ['id', 'branch', 'branch_name', 'product', 'product_name', 'quantity', 'date_requested', 'status']
        read_only_fields = ['id', 'date_requested']
