from dateutil.relativedelta import relativedelta
from datetime import timedelta
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, F, Count, IntegerField
from django.db.models.functions import Coalesce, Cast
from .serializers import (
    ProductInflowSerializer,
    ProductOutflowSerializer,
    InwardQtyReportSerializer,
    OutwardQtyReportSerializer,
    BranchWiseQtyReportSerializer,
    ExpiredProductReportSerializer,
    OpenedProductReportSerializer,
    ClosedProductReportSerializer,
    DailyReportSerializer,
    ProductDetailsReportSerializer,
    SupplierWiseProductReportSerializer,
    BranchDailyReportSerializer,
    BranchExpiredProductReportSerializer,
    BranchProductDetailsReportSerializer,
    BranchOverviewSerializer,
    TopProductsSerializer,
    ProductRequestStatusSerializer,
    ProductOutflowDashboardSerializer,
    BranchProductInventorySerializer,
)
from apps.products.models import Product
from apps.branches.models import Branch, BranchProduct, ProductRequest
from .models import ProductInflow, ProductOutflow


class ProductInflowViewSet(viewsets.ModelViewSet):
    queryset = ProductInflow.objects.all()
    serializer_class = ProductInflowSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductOutflowViewSet(viewsets.ModelViewSet):
    queryset = ProductOutflow.objects.all()
    serializer_class = ProductOutflowSerializer
    permission_classes = [permissions.IsAuthenticated]


class InwardQtyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        inflows = (
            ProductInflow.objects.values(
                "product__name", "supplier__name", "expiry_date"
            )
            .annotate(total_quantity=Sum("quantity_received"))
            .order_by("-total_quantity")
        )
        serializer = InwardQtyReportSerializer(inflows, many=True)
        return Response(serializer.data)


class OutwardQtyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        outflows = (
            ProductOutflow.objects.values(
                "product__name", "branch__name", "expiry_date"
            )
            .annotate(total_quantity=Sum("quantity_sent"))
            .order_by("-total_quantity")
        )
        serializer = OutwardQtyReportSerializer(outflows, many=True)
        return Response(serializer.data)


class BranchWiseQtyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch_products = (
            BranchProduct.objects.values("branch__name", "product__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("branch__name", "-total_quantity")
        )
        serializer = BranchWiseQtyReportSerializer(branch_products, many=True)
        return Response(serializer.data)


class ExpiredProductReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        expired_products = (
            ProductInflow.objects.filter(expiry_date__lte=today)
            .values("product__name", "expiry_date")
            .annotate(quantity=Sum("quantity_received"))
            .order_by("expiry_date")
        )
        serializer = ExpiredProductReportSerializer(expired_products, many=True)
        return Response(serializer.data)


class SupplierWiseProductReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        supplier_products = (
            ProductInflow.objects.values("supplier__name", "product__name")
            .annotate(total_quantity=Sum("quantity_received"))
            .order_by("supplier__name", "-total_quantity")
        )
        serializer = SupplierWiseProductReportSerializer(supplier_products, many=True)
        return Response(serializer.data)


class OpenedProductReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        opened_products = (
            BranchProduct.objects.filter(status="active")
            .values("product__name", "branch__name")
            .annotate(quantity=Sum("quantity"))
            .order_by("-quantity")
        )
        serializer = OpenedProductReportSerializer(opened_products, many=True)
        return Response(serializer.data)


class ClosedProductReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        closed_products = (
            BranchProduct.objects.filter(status="inactive")
            .values("product__name", "branch__name")
            .annotate(quantity=Sum("quantity"))
            .order_by("-quantity")
        )
        serializer = ClosedProductReportSerializer(closed_products, many=True)
        return Response(serializer.data)


class DailyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        inflows = ProductInflow.objects.filter(date_received=today)
        outflows = ProductOutflow.objects.filter(date_sent=today)
        data = {
            "inflows": inflows,
            "outflows": outflows,
        }
        serializer = DailyReportSerializer(data)
        return Response(serializer.data)


class ProductDetailsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.annotate(
            total_inflow=Sum("productinflow__quantity_received"),
            total_outflow=Sum("productoutflow__quantity_sent"),
            closing_stock=F("quantity"),
        ).values("name", "sku", "total_inflow", "total_outflow", "closing_stock")
        serializer = ProductDetailsReportSerializer(products, many=True)
        return Response(serializer.data)


class BranchDailyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch = request.user.managed_branch
        today = timezone.now().date()

        inflows = ProductRequest.objects.filter(
            branch=branch, status="fulfilled", date_requested__date=today
        )

        data = {
            "inflows": inflows,
        }

        serializer = BranchDailyReportSerializer(data)
        return Response(serializer.data)


class BranchProductDetailsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch = request.user.managed_branch
        branch_products = BranchProduct.objects.filter(branch=branch).select_related(
            "product"
        )

        products = [
            {
                "name": bp.product.name,
                "sku": bp.product.sku,
                "quantity": bp.quantity,
                "status": bp.status,
            }
            for bp in branch_products
        ]

        serializer = BranchProductDetailsReportSerializer(products, many=True)
        return Response(serializer.data)


class BranchExpiredProductReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch = request.user.managed_branch
        today = timezone.now().date()

        expired_products = (
            BranchProduct.objects.filter(
                branch=branch, product__productinflow__expiry_date__lte=today
            )
            .annotate(
                product_name=F("product__name"),
                expiry_date=F("product__productinflow__expiry_date"),
            )
            .values("product_name", "expiry_date", "quantity")
        )

        serializer = BranchExpiredProductReportSerializer(expired_products, many=True)
        return Response(serializer.data)


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get query parameters for time period filtering
        period = request.query_params.get("period", "daily")

        # Calculate date range based on the period
        end_date = timezone.now().date()
        if period == "daily":
            start_date = end_date
        elif period == "monthly":
            start_date = end_date - relativedelta(months=1)
        elif period == "yearly":
            start_date = end_date - relativedelta(years=1)
        else:
            return Response({"error": "Invalid period specified"}, status=400)

        # Fetch data for different sections of the dashboard
        total_products = Product.objects.count()
        total_branches = Branch.objects.count()

        inflow_data = ProductInflow.objects.filter(
            date_received__range=[start_date, end_date]
        ).aggregate(
            total_inflow=Coalesce(Sum("quantity_received"), 0),
            total_inflow_value=Coalesce(
                Sum(
                    F("quantity_received") * F("product__price"),
                    output_field=IntegerField(),
                ),
                0,
            ),
        )

        outflow_data = ProductOutflow.objects.filter(
            date_sent__range=[start_date, end_date]
        ).aggregate(
            total_outflow=Coalesce(Sum("quantity_sent"), 0),
            total_outflow_value=Coalesce(
                Sum(
                    F("quantity_sent") * F("product__price"),
                    output_field=IntegerField(),
                ),
                0,
            ),
        )

        top_products = Product.objects.annotate(
            total_outflow=Coalesce(Sum("productoutflow__quantity_sent"), 0)
        ).order_by("-total_outflow")[:5]

        low_stock_products = Product.objects.filter(quantity__lte=10).count()

        branch_stock = (
            BranchProduct.objects.values("branch__name")
            .annotate(total_stock=Sum("quantity"))
            .order_by("-total_stock")[:5]
        )

        expired_products = (
            ProductInflow.objects.filter(expiry_date__lte=end_date)
            .values("product__name")
            .annotate(total_expired=Sum("quantity_received"))
            .order_by("-total_expired")[:5]
        )

        # Prepare the response data
        response_data = {
            "total_products": total_products,
            "total_branches": total_branches,
            "total_inflow": inflow_data["total_inflow"],
            "total_inflow_value": float(inflow_data["total_inflow_value"]),
            "total_outflow": outflow_data["total_outflow"],
            "total_outflow_value": float(outflow_data["total_outflow_value"]),
            "top_products": [
                {"name": product.name, "total_outflow": product.total_outflow}
                for product in top_products
            ],
            "low_stock_products": low_stock_products,
            "branch_stock": list(branch_stock),
            "expired_products": list(expired_products),
        }

        return Response(response_data)


class BranchDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch = request.user.managed_branch
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        # Branch overview
        total_products = BranchProduct.objects.filter(branch=branch).count()
        active_products = BranchProduct.objects.filter(
            branch=branch, status="active"
        ).count()
        total_requests = ProductRequest.objects.filter(branch=branch).count()
        pending_requests = ProductRequest.objects.filter(
            branch=branch, status="pending"
        ).count()

        overview = {
            "total_products": total_products,
            "active_products": active_products,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
        }

        # Top 5 products by quantity
        top_products = (
            BranchProduct.objects.filter(branch=branch)
            .order_by("-quantity")[:5]
            .values("product__name", "quantity")
        )

        # Product request status
        request_status = (
            ProductRequest.objects.filter(branch=branch)
            .values("status")
            .annotate(count=Count("status"))
        )

        # Product outflow in the last 30 days
        product_outflow = (
            ProductOutflow.objects.filter(branch=branch, date_sent__gte=last_30_days)
            .values("date_sent")
            .annotate(total_quantity=Sum("quantity_sent"))
            .order_by("date_sent")
        )

        # Current inventory levels
        inventory_levels = BranchProduct.objects.filter(branch=branch).values(
            "product__name", "quantity"
        )

        serialized_data = {
            "overview": BranchOverviewSerializer(overview).data,
            "top_products": TopProductsSerializer(top_products, many=True).data,
            "request_status": ProductRequestStatusSerializer(
                request_status, many=True
            ).data,
            "product_outflow": ProductOutflowDashboardSerializer(
                product_outflow, many=True
            ).data,
            "inventory_levels": BranchProductInventorySerializer(
                inventory_levels, many=True
            ).data,
        }

        return Response(serialized_data)
