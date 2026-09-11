from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('', views.purchasing_dashboard, name='dashboard'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('orders/', views.po_list, name='po_list'),
    path('orders/<int:pk>/', views.po_detail, name='po_detail'),
]
