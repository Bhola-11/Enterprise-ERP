from django.urls import path
from . import views

app_name = 'subcontracting'

urlpatterns = [
    path('', views.subcontract_dashboard, name='dashboard'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
]
