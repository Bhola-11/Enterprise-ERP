from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, ProductViewSet, SalesOrderViewSet,
    InvoiceViewSet, EmployeeViewSet, SupportTicketViewSet,
    ProjectViewSet, StockMovementViewSet
)

app_name = 'api'

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', SalesOrderViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'tickets', SupportTicketViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'stock-movements', StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
