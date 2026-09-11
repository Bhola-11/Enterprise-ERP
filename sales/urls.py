from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
]
