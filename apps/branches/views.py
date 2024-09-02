from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import PermissionDenied
from .serializers import (
    BranchSerializer,
    ProductRequestSerializer,
    BranchProductSerializer,
    UpdateBranchProductQuantitySerializer,
)
from .models import Branch, ProductRequest, BranchProduct


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Branch.objects.all()
        elif user.role == 'branch_manager':
            return Branch.objects.filter(manager=user)
        return Branch.objects.none()

    def perform_update(self, serializer):
        if self.request.user.role != 'branch_manager':
            raise PermissionDenied("Only branch managers can update branch details.")
        serializer.save()


class BranchProductViewSet(viewsets.ModelViewSet):
    queryset = BranchProduct.objects.all()
    serializer_class = BranchProductSerializer

    def get_queryset(self):
        branch = self.request.user.managed_branch
        return BranchProduct.objects.filter(branch=branch)

    @action(detail=True, methods=["post"])
    def update_quantity(self, request, pk=None):
        branch_product = self.get_object()
        serializer = UpdateBranchProductQuantitySerializer(
            branch_product, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ProductRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "branch_manager":
            return ProductRequest.objects.filter(branch=user.managed_branch)
        return ProductRequest.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == "branch_manager":
            serializer.save(branch=user.managed_branch)
        else:
            serializer.save()
