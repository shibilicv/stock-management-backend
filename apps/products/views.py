from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from .serializers import ProductSerializer, DamagedProductSerializer
from .models import Product, DamagedProduct


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["name"]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["name", "price"]


class DamagedProductViewSet(viewsets.ModelViewSet):
    queryset = DamagedProduct.objects.all()
    serializer_class = DamagedProductSerializer
    permission_classes = [permissions.IsAuthenticated]
