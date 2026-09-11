from django.urls import path
from . import views

app_name = 'manufacturing'

urlpatterns = [
    path('', views.manufacturing_dashboard, name='dashboard'),
    path('boms/', views.bom_list, name='bom_list'),
    path('boms/<int:pk>/', views.bom_detail, name='bom_detail'),
    path('orders/', views.production_order_list, name='order_list'),
    path('orders/add/', views.production_order_create, name='order_create'),
    path('orders/<int:pk>/', views.production_order_detail, name='order_detail'),
]
